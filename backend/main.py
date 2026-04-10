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
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

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

# ── DETECT COLUMNS ────────────────────────────────────────────
@app.post("/api/detect-columns")
async def detect_columns(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return JSONResponse({"status": "error", "message": "CSV file is empty"})
        columns = [c.strip() for c in rows[0].keys()]
        sample_row = {k.strip(): str(v)[:150] for k, v in rows[0].items()}
        mapping = {}
        for col in columns:
            c = col.lower().strip()
            if any(k in c for k in ["participant_id", "participant", "student_id", "student", "id"]):
                if "participant_id" not in mapping:
                    mapping["participant_id"] = col
            elif any(k in c for k in ["simulation", "sim", "course", "scenario", "assignment"]):
                if "simulation" not in mapping:
                    mapping["simulation"] = col
            elif any(k in c for k in ["completed", "status", "done", "finish"]):
                if "completed_user" not in mapping:
                    mapping["completed_user"] = col
            elif any(k in c for k in ["transcript_user", "user_transcript", "interview", "script_a", "transcript_a"]):
                mapping["transcript_user"] = col
            elif any(k in c for k in ["transcript_client", "client_transcript", "client", "script_b", "transcript_b"]):
                mapping["transcript_client"] = col
            elif any(k in c for k in ["duration_user", "duration_seconds_user"]):
                mapping["duration_seconds_user"] = col
            elif any(k in c for k in ["duration_client", "duration_seconds_client"]):
                mapping["duration_seconds_client"] = col
        # Fallback: long text columns are likely transcripts
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
    selected_indicators: Optional[str] = Form(None),
    setup_data: Optional[str] = Form(None)
):
    try:
        # Load rubric
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

        # Parse setup data
        setup = None
        if setup_data:
            try:
                setup = json.loads(setup_data)
            except Exception:
                setup = None

        # Read CSV
        contents = await file.read()
        text = contents.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return JSONResponse({"status": "error", "message": "No data found in CSV"})

        # Apply column mapping
        if col_map:
            inv_map = {v: k for k, v in col_map.items()}
            mapped_rows = []
            for row in rows:
                new_row = {}
                for col, val in row.items():
                    standard = inv_map.get(col.strip(), col.strip())
                    new_row[standard] = val
                mapped_rows.append(new_row)
            rows = mapped_rows

        # Evaluate each participant
        students = []
        for i, row in enumerate(rows):
            print(f"\nEvaluating participant {i+1}/{len(rows)}")
            result = evaluate_participant(
                row,
                rubric_text=rubric_text,
                selected_indicators=sel_inds,
                setup_data=setup
            )
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
        client = anthropic.Anthropic(api_key=os.getenv("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"))
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

# ── EXPORT PDF (Professional) ─────────────────────────────────
@app.post("/api/export/pdf")
async def export_pdf(request: dict):
    students = request.get("students", [])
    setup = request.get("setup_data", {})
    if not students:
        return JSONResponse({"status": "error", "message": "No data to export"})

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title Page ──
    title_style = ParagraphStyle('Title', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#0f172a'),
        spaceAfter=6, alignment=TA_LEFT)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#64748b'),
        spaceAfter=4)
    head_style = ParagraphStyle('Head', parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#1e3a5f'),
        spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=9.5, textColor=colors.HexColor('#334155'),
        leading=14, spaceAfter=4)
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#64748b'),
        spaceAfter=2, fontName='Helvetica-Bold')
    score_style = ParagraphStyle('Score', parent=styles['Normal'],
        fontSize=9.5, textColor=colors.HexColor('#0f172a'),
        leading=13, spaceAfter=3)

    from datetime import datetime
    story.append(Paragraph("RubricAI v2", title_style))
    story.append(Paragraph("Class Evaluation Report", ParagraphStyle('Sub2',
        parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#3b82f6'),
        spaceAfter=4)))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", sub_style))
    if setup.get("course"):
        story.append(Paragraph(f"Course: {setup['course']}", sub_style))
    if setup.get("cohort"):
        story.append(Paragraph(f"Cohort: {setup['cohort']}", sub_style))
    story.append(Paragraph("CPS LEARN Lab · Northeastern University", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5,
        color=colors.HexColor('#3b82f6'), spaceAfter=16))

    # ── Summary Table ──
    story.append(Paragraph("Cohort Summary", head_style))
    tot = len(students)
    comp = sum(1 for s in students if s.get("completed") == 1)
    comm_vals = [s["comm_user"] for s in students if s.get("comm_user") is not None]
    ct_vals = [s["ct_user"] for s in students if s.get("ct_user") is not None]
    avg_comm = f"{sum(comm_vals)/len(comm_vals):.2f}" if comm_vals else "N/A"
    avg_ct = f"{sum(ct_vals)/len(ct_vals):.2f}" if ct_vals else "N/A"

    summary_data = [
        ["Total Participants", "Completed", "Avg Comm Score", "Avg CT Score"],
        [str(tot), str(comp), avg_comm, avg_ct]
    ]
    summary_table = Table(summary_data, colWidths=[1.5*inch]*4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#64748b')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 13),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,1), [colors.white]),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # ── Per Student ──
    story.append(Paragraph("Individual Evaluation Reports", head_style))
    story.append(HRFlowable(width="100%", thickness=0.5,
        color=colors.HexColor('#e2e8f0'), spaceAfter=12))

    level_map = {1: "Beginning", 2: "Developing", 3: "Applying", 4: "Mastery"}
    score_colors = {1: '#ef4444', 2: '#f97316', 3: '#f59e0b', 4: '#10b981'}

    for s in students:
        pid = s.get("participant_id", "N/A")
        sim = s.get("simulation", "N/A")
        completed = "Completed" if s.get("completed") == 1 else "Incomplete"

        # Student header
        story.append(Paragraph(
            f"<b>{pid}</b> &nbsp;·&nbsp; {sim} &nbsp;·&nbsp; {completed}",
            ParagraphStyle('SHead', parent=styles['Normal'],
                fontSize=11, textColor=colors.HexColor('#0f172a'),
                backColor=colors.HexColor('#f8fafc'),
                borderPad=6, spaceBefore=10, spaceAfter=6,
                borderColor=colors.HexColor('#e2e8f0'), borderWidth=0.5)
        ))

        # Score summary
        score_row = [
            ["User Interview Comm", "User Interview CT", "Client Conv Comm", "Client Conv CT"],
            [
                str(s.get("comm_user") or "N/A"),
                str(s.get("ct_user") or "N/A"),
                str(s.get("comm_client") or "N/A"),
                str(s.get("ct_client") or "N/A")
            ]
        ]
        score_table = Table(score_row, colWidths=[1.5*inch]*4)
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#64748b')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,1), (-1,1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 8))

        # Indicator details
        detail = s.get("_detail", {})
        for sess_key, sess_label in [("user", "User Interview"), ("client", "Client Conversation")]:
            sess_data = detail.get(sess_key, {})
            if not sess_data:
                continue
            story.append(Paragraph(sess_label, ParagraphStyle('SessLabel',
                parent=styles['Normal'], fontSize=9,
                textColor=colors.HexColor('#3b82f6'),
                fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4)))

            # Summary
            if sess_data.get("summary"):
                story.append(Paragraph(sess_data["summary"], body_style))

            # Indicator table
            ind_table_data = [["Indicator", "Score", "Level", "Rationale", "Feedback", "Evidence"]]
            for ind, data in sess_data.get("scores", {}).items():
                sc = data.get("score", 0)
                lvl = level_map.get(sc, "N/A")
                rat = data.get("rationale", "")
                fb = data.get("feedback", "")
                quotes = data.get("quotes", [])
                ev = quotes[0] if quotes else ""
                ind_table_data.append([
                    Paragraph(f"<b>{ind}</b>", score_style),
                    Paragraph(f"<b>{sc}</b>", score_style),
                    Paragraph(lvl, score_style),
                    Paragraph(rat, body_style),
                    Paragraph(fb, body_style),
                    Paragraph(f'"{ev}"' if ev else "", body_style)
                ])

            if len(ind_table_data) > 1:
                ind_table = Table(ind_table_data,
                    colWidths=[0.7*inch, 0.45*inch, 0.7*inch, 1.8*inch, 1.8*inch, 1.5*inch])
                ind_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#64748b')),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('ALIGN', (0,0), (2,-1), 'CENTER'),
                    ('ALIGN', (3,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                    ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1),
                        [colors.white, colors.HexColor('#f8fafc')]),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(ind_table)
                story.append(Spacer(1, 6))

        story.append(HRFlowable(width="100%", thickness=0.5,
            color=colors.HexColor('#e2e8f0'), spaceAfter=10))

    # ── Footer ──
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#94a3b8'))
        canvas.drawString(0.75*inch, 0.4*inch,
            "RubricAI v2 · CPS LEARN Lab · Northeastern University · Confidential Research Record")
        canvas.drawRightString(letter[0] - 0.75*inch, 0.4*inch,
            f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=rubricai_report.pdf"}
    )
