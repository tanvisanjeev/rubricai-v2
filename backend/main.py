import os
import csv
import json
import io
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import anthropic
from evaluator import evaluate_participant, load_rubric
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "RubricAI v2 backend running"}

# ── COLUMN DETECTION ──────────────────────────────────────────
@app.post("/api/detect-columns")
async def detect_columns(file: UploadFile = File(...)):
    """Auto-detect column mappings from any CSV file"""
    try:
        contents = await file.read()
        text = contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return JSONResponse({"status": "error", "message": "CSV file is empty"})

        columns = [c.strip() for c in rows[0].keys()]
        sample_row = {k.strip(): str(v)[:150] for k, v in rows[0].items()}

        # Smart column detection
        mapping = {}
        for col in columns:
            c = col.lower().strip()
            val_len = len(str(rows[0].get(col, "")))

            # Student ID
            if any(k in c for k in ["participant_id", "participant", "student_id", "student", "id"]):
                if "participant_id" not in mapping:
                    mapping["participant_id"] = col
            # Simulation/course
            elif any(k in c for k in ["simulation", "sim", "course", "scenario", "assignment"]):
                if "simulation" not in mapping:
                    mapping["simulation"] = col
            # Completion status
            elif any(k in c for k in ["completed", "status", "done", "finish"]):
                if "completed_user" not in mapping:
                    mapping["completed_user"] = col
            # User transcript (long text)
            elif any(k in c for k in ["transcript_user", "user_transcript", "interview", "script_a", "transcript_a", "user_session"]):
                mapping["transcript_user"] = col
            # Client transcript (long text)
            elif any(k in c for k in ["transcript_client", "client_transcript", "client", "script_b", "transcript_b", "client_session"]):
                mapping["transcript_client"] = col
            # Duration user
            elif any(k in c for k in ["duration_user", "duration_seconds_user", "user_duration"]):
                mapping["duration_seconds_user"] = col
            # Duration client
            elif any(k in c for k in ["duration_client", "duration_seconds_client", "client_duration"]):
                mapping["duration_seconds_client"] = col

        # Fallback: detect long text columns as transcripts
        for col in columns:
            if col not in mapping.values():
                avg_len = sum(len(str(r.get(col, ""))) for r in rows[:3]) / 3
                if avg_len > 300:
                    if "transcript_user" not in mapping:
                        mapping["transcript_user"] = col
                    elif "transcript_client" not in mapping:
                        mapping["transcript_client"] = col

        return JSONResponse({
            "status": "success",
            "columns": columns,
            "suggested_mapping": mapping,
            "total_rows": len(rows),
            "sample": sample_row
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# ── EVALUATE ──────────────────────────────────────────────────
@app.post("/api/evaluate")
async def evaluate(
    file: UploadFile = File(...),
    rubric: Optional[UploadFile] = File(None),
    column_mapping: Optional[str] = Form(None),
    selected_indicators: Optional[str] = Form(None)
):
    try:
        # Save rubric if uploaded
        rubric_text = None
        if rubric and rubric.filename:
            rubric_contents = await rubric.read()
            rubric_text = rubric_contents.decode("utf-8")
            rubric_path = os.path.join(os.path.dirname(__file__), "rubric.md")
            with open(rubric_path, "w") as f:
                f.write(rubric_text)
        else:
            rubric_text = load_rubric()

        # Parse selected indicators
        sel_inds = None
        if selected_indicators:
            try:
                sel_inds = json.loads(selected_indicators)
            except Exception:
                sel_inds = None

        # Parse column mapping
        col_map = None
        if column_mapping:
            try:
                col_map = json.loads(column_mapping)
            except Exception:
                col_map = None

        # Read CSV
        contents = await file.read()
        text = contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return JSONResponse({"status": "error", "message": "No data found in CSV"})

        # Apply column mapping — rename columns to standard names
        if col_map:
            # Invert: file_col -> standard_col
            inv_map = {v: k for k, v in col_map.items()}
            mapped_rows = []
            for row in rows:
                new_row = {}
                for col, val in row.items():
                    standard = inv_map.get(col.strip(), col.strip())
                    new_row[standard] = val
                mapped_rows.append(new_row)
            rows = mapped_rows

        # Evaluate each student
        students = []
        for i, row in enumerate(rows):
            print(f"Evaluating student {i+1}/{len(rows)}")
            result = evaluate_participant(row, rubric_text=rubric_text, selected_indicators=sel_inds)
            if result:
                students.append(result)

        return JSONResponse({
            "status": "success",
            "students": students,
            "total": len(students)
        })
    except Exception as e:
        print(f"Evaluation error: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

# ── CHAT ──────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: dict):
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        messages = request.get("messages", [])
        system = request.get("system", "You are a helpful educational assessment assistant.")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=messages
        )
        return JSONResponse({"status": "success", "reply": response.content[0].text})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# ── EXPORT CSV ────────────────────────────────────────────────
@app.post("/api/export/csv")
async def export_csv(request: dict):
    students = request.get("students", [])
    if not students:
        return JSONResponse({"status": "error", "message": "No data to export"})

    output = io.StringIO()
    score_keys = sorted(set(k for s in students for k in s.keys() if k.endswith("_score")))
    fieldnames = ["participant_id", "simulation", "completed",
                  "comm_user", "ct_user", "comm_client", "ct_client"] + score_keys

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for s in students:
        writer.writerow({k: s.get(k, "") for k in fieldnames})

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rubricai_scores.csv"}
    )

# ── EXPORT PDF ────────────────────────────────────────────────
@app.post("/api/export/pdf")
async def export_pdf(request: dict):
    students = request.get("students", [])
    if not students:
        return JSONResponse({"status": "error", "message": "No data to export"})

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    w, h = letter

    def new_page_header():
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0.23, 0.51, 0.96)
        c.drawString(50, h - 40, "RubricAI v2 — Class Evaluation Report")
        c.setFillColorRGB(0.4, 0.5, 0.6)
        c.setFont("Helvetica", 9)
        c.drawString(50, h - 55, "CPS LEARN Lab · Northeastern University")
        c.setStrokeColorRGB(0.23, 0.51, 0.96)
        c.line(50, h - 62, w - 50, h - 62)
        return h - 80

    y = new_page_header()

    for s in students:
        if y < 120:
            c.showPage()
            y = new_page_header()

        # Student header
        c.setFillColorRGB(0.1, 0.1, 0.2)
        c.rect(50, y - 4, w - 100, 22, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(56, y + 6, f"{s.get('participant_id', 'N/A')}  ·  {s.get('simulation', 'N/A')}  ·  {'Completed' if s.get('completed') else 'Incomplete'}")
        y -= 30

        # Score summary
        c.setFillColorRGB(0.2, 0.2, 0.3)
        c.setFont("Helvetica", 10)
        c.drawString(56, y, f"User Interview — Comm: {s.get('comm_user', 'N/A')}  |  CT: {s.get('ct_user', 'N/A')}     Client Conversation — Comm: {s.get('comm_client', 'N/A')}  |  CT: {s.get('ct_client', 'N/A')}")
        y -= 20

        # Indicator details from _detail
        detail = s.get("_detail", {})
        for sess_key, sess_label in [("user", "User Interview"), ("client", "Client Conversation")]:
            sess_data = detail.get(sess_key, {})
            if not sess_data:
                continue
            c.setFont("Helvetica-Bold", 9)
            c.setFillColorRGB(0.23, 0.51, 0.96)
            c.drawString(56, y, sess_label)
            y -= 14
            for ind, data in sess_data.get("scores", {}).items():
                if y < 80:
                    c.showPage()
                    y = new_page_header()
                score = data.get("score", "N/A")
                feedback = data.get("feedback", "")
                c.setFont("Helvetica-Bold", 9)
                c.setFillColorRGB(0.1, 0.1, 0.2)
                c.drawString(66, y, f"{ind} — Score: {score}/4")
                y -= 12
                if feedback:
                    c.setFont("Helvetica", 8)
                    c.setFillColorRGB(0.4, 0.4, 0.5)
                    # Wrap long feedback
                    words = feedback.split()
                    line = ""
                    for word in words:
                        if len(line + word) < 90:
                            line += word + " "
                        else:
                            c.drawString(76, y, line.strip())
                            y -= 11
                            line = word + " "
                    if line:
                        c.drawString(76, y, line.strip())
                        y -= 11
            y -= 8

        y -= 10
        c.setStrokeColorRGB(0.8, 0.8, 0.9)
        c.line(50, y, w - 50, y)
        y -= 14

    c.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=rubricai_report.pdf"}
    )
