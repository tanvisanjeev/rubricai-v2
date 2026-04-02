from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from evaluator import (
    evaluate_participant, load_rubric,
    USER_INDICATORS, CLIENT_INDICATORS, SCORE_LABELS,
    COMM_USER, CT_USER, COMM_CLIENT, CT_CLIENT, compute_average
)
from pdf_exporter import generate_pdf
import csv
import io
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
chat_model = genai.GenerativeModel("gemini-2.5-flash-lite")

app = FastAPI(title="RubricAI API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "RubricAI API",
        "version": "2.0",
        "status": "operational"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "model": "gemini-2.5-flash-lite",
        "provider": "Google Gemini",
        "temperature": 0,
        "user_indicators": len(USER_INDICATORS),
        "client_indicators": len(CLIENT_INDICATORS),
        "total_indicators": len(USER_INDICATORS) + len(CLIENT_INDICATORS),
    }


@app.post("/api/evaluate")
async def evaluate_csv(
    file: UploadFile = File(...),
    rubric: UploadFile = File(None)
):
    try:
        contents = await file.read()
        text = contents.decode("utf-8")
        if text.startswith("\ufeff"):
            text = text[1:]

        reader = csv.DictReader(io.StringIO(text))
        rows = [r for r in reader if r.get("participant_id", "").strip()]

        if not rows:
            return {"status": "error", "message": "No valid rows found. Check participant_id column."}

        required = {"participant_id", "simulation", "transcript_user", "transcript_client"}
        missing = required - set(rows[0].keys())
        if missing:
            return {"status": "error", "message": f"Missing columns: {missing}"}

        # Load rubric — if uploaded save to disk once, then all calls read from disk
        if rubric and rubric.filename:
            rubric_contents = await rubric.read()
            rubric_text = rubric_contents.decode("utf-8")
            rubric_path = os.path.join(os.path.dirname(__file__), "rubric.md")
            with open(rubric_path, "w") as f:
                f.write(rubric_text)
        else:
            rubric_text = load_rubric()

        if not rubric_text:
            return {"status": "error", "message": "Rubric not found. Please upload a rubric file or add rubric.md to the backend directory."}

        students = []
        for row in rows:
            pid        = row["participant_id"].strip()
            sim        = row.get("simulation", "unknown").strip()
            tx_user    = row.get("transcript_user", "").strip()
            tx_client  = row.get("transcript_client", "").strip()
            dur_user   = int(row.get("duration_seconds_user", 0) or 0)
            dur_client = int(float(row.get("duration_seconds_client", 0) or 0))
            completed  = row.get("completed_user", "").strip()
            notes      = row.get("notes", "").strip()

            result = evaluate_participant(
                participant_id    = pid,
                simulation        = sim,
                transcript_user   = tx_user,
                transcript_client = tx_client,
                duration_user     = dur_user,
                duration_client   = dur_client,
                rubric_text       = rubric_text,
            )

            flat = {
                "id":             pid,
                "participant_id": pid,
                "simulation":     sim,
                "duration":       dur_user or dur_client,
                "completed":      1 if completed == "Complete" else 0,
                "notes":          notes,
            }

            user_s = result.get("user")
            if user_s:
                for key in USER_INDICATORS:
                    item = user_s["scores"].get(key, {})
                    flat[f"{key}_user_score"] = item.get("score", 0)
                    flat[f"{key}_user_level"] = item.get("level", "N/A")
                flat["comm_user"] = user_s.get("comm_avg")
                flat["ct_user"]   = user_s.get("ct_avg")
            else:
                for key in USER_INDICATORS:
                    flat[f"{key}_user_score"] = 0
                    flat[f"{key}_user_level"] = "N/A"
                flat["comm_user"] = None
                flat["ct_user"]   = None

            client_s = result.get("client")
            if client_s:
                for key in CLIENT_INDICATORS:
                    item = client_s["scores"].get(key, {})
                    flat[f"{key}_client_score"] = item.get("score", 0)
                    flat[f"{key}_client_level"] = item.get("level", "N/A")
                flat["comm_client"] = client_s.get("comm_avg")
                flat["ct_client"]   = client_s.get("ct_avg")
            else:
                for key in CLIENT_INDICATORS:
                    flat[f"{key}_client_score"] = 0
                    flat[f"{key}_client_level"] = "N/A"
                flat["comm_client"] = None
                flat["ct_client"]   = None

            flat["_detail"] = result
            students.append(flat)

        return {"status": "success", "students": students, "total": len(students)}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/evaluate/single")
async def evaluate_single(data: dict):
    try:
        rubric_text = load_rubric()
        result = evaluate_participant(
            participant_id    = data.get("participant_id", "TEST"),
            simulation        = data.get("simulation", "unknown"),
            transcript_user   = data.get("transcript_user", ""),
            transcript_client = data.get("transcript_client", ""),
            duration_user     = data.get("duration_user", 0),
            duration_client   = data.get("duration_client", 0),
            rubric_text       = rubric_text,
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/export/csv")
async def export_csv(data: dict):
    try:
        students = data.get("students", [])
        if not students:
            return {"status": "error", "message": "No students to export."}

        fieldnames = [k for k in students[0].keys() if k != "_detail"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for s in students:
            row = {k: v for k, v in s.items() if k != "_detail"}
            writer.writerow(row)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rubric_scores.csv"}
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/export/pdf")
async def export_pdf(data: dict):
    try:
        students  = data.get("students", [])
        pdf_bytes = generate_pdf(students)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=rubric_scores.pdf"}
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/chat")
async def chat(data: dict):
    try:
        system_prompt = data.get("system", "You are a helpful assessment assistant.")
        messages      = data.get("messages", [])
        if not messages:
            return {"status": "error", "message": "No messages provided."}

        last_message = messages[-1]["content"]
        full_prompt  = f"{system_prompt}\n\n{last_message}"

        response = chat_model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=1000,
            )
        )
        return {"status": "success", "reply": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
