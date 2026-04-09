import os
import json
import time
import anthropic

def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def load_rubric(rubric_text=None):
    if rubric_text:
        return rubric_text
    rubric_path = os.path.join(os.path.dirname(__file__), "rubric.md")
    if os.path.exists(rubric_path):
        with open(rubric_path, "r") as f:
            return f.read()
    return ""

def evaluate_session(transcript, participant_id, session_type, duration=0, rubric_text=None, selected_indicators=None):
    if not rubric_text:
        rubric_text = load_rubric()

    rubric_section = rubric_text[:4000]
    transcript_section = str(transcript)[:4000]

    # Default indicator lists (fallback if rubric not parsed)
    if session_type == "user_interview":
        default_indicators = ["C1_I1", "C1_I2", "C1_I3", "C1_I5", "C1_I6", "CT1_I1", "CT1_I3"]
    else:
        default_indicators = ["C2_I1", "C2_I2", "C2_I3", "CT2_I1", "CT2_I2", "CT2_I3", "CT2_I4", "CT3_I1", "CT3_I2", "CT3_I4"]

    # ── FIXED: use selected indicators directly, don't filter against hardcoded list ──
    if selected_indicators and len(selected_indicators) > 0:
        indicators_to_use = list(selected_indicators)
        if not indicators_to_use:
            indicators_to_use = default_indicators
    else:
        indicators_to_use = default_indicators

    ind_list = ", ".join(indicators_to_use)

    prompt = f"""You are an expert rubric-based educational assessor evaluating student interview performance.

PARTICIPANT ID: {participant_id}
SESSION TYPE: {session_type}
DURATION: {duration} seconds

RUBRIC (use this to score):
{rubric_section}

TRANSCRIPT TO EVALUATE:
{transcript_section}

INSTRUCTIONS:
Evaluate ONLY these indicators: {ind_list}
Score each on a 1-4 scale based strictly on the rubric criteria.
For each indicator provide:
- score: integer 1, 2, 3, or 4
- rationale: 2-3 sentences explaining why this score was given, referencing the rubric
- feedback: 1-2 sentences of specific, actionable advice to improve
- quotes: up to 2 direct quotes from the transcript that support the score

Also provide:
- comm_score: average of communication indicator scores (float)
- ct_score: average of critical thinking indicator scores (float)
- summary: 2-3 sentence overall summary of this participant's performance in this session

Return ONLY valid JSON, no markdown, no extra text:
{{
  "scores": {{
    "INDICATOR_ID": {{
      "score": 2,
      "rationale": "explanation referencing rubric criteria",
      "feedback": "specific actionable improvement advice",
      "quotes": ["direct quote from transcript"]
    }}
  }},
  "comm_score": 2.1,
  "ct_score": 1.8,
  "summary": "overall performance summary"
}}"""

    try:
        client = get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Strip markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error evaluating {participant_id} {session_type}: {e}")
        return None

def get_col(row, *keys, default=""):
    """Flexible column extraction — handles different naming conventions"""
    for k in keys:
        if k in row and row[k]:
            return row[k]
    # Case-insensitive fallback
    row_lower = {str(k).lower().strip(): v for k, v in row.items()}
    for k in keys:
        if str(k).lower() in row_lower and row_lower[str(k).lower()]:
            return row_lower[str(k).lower()]
    return default

def evaluate_participant(row, rubric_text=None, selected_indicators=None):
    pid = get_col(row, "participant_id", "student_id", "id", "student", "name", "participant")
    simulation = get_col(row, "simulation", "sim", "course", "assignment", "session_name", "scenario")
    transcript_user = get_col(row, "transcript_user", "user_transcript", "interview_transcript",
                               "transcript_a", "script_a", "user_session", "interview")
    transcript_client = get_col(row, "transcript_client", "client_transcript", "client_conversation",
                                 "transcript_b", "script_b", "client_session", "client")
    duration_user = get_col(row, "duration_seconds_user", "duration_user", "user_duration", default=0)
    duration_client = get_col(row, "duration_seconds_client", "duration_client", "client_duration", default=0)
    completed_user = get_col(row, "completed_user", "completed", "status", default="Complete")

    result = {
        "participant_id": str(pid) if pid else "unknown",
        "simulation": str(simulation) if simulation else "unknown",
        "completed": 1 if str(completed_user).lower() in ["complete", "yes", "1", "true", "y"] else 0,
        "comm_user": None, "ct_user": None,
        "comm_client": None, "ct_client": None,
        "_detail": {}
    }

    # Evaluate user interview session
    if transcript_user and len(str(transcript_user).strip()) > 100:
        time.sleep(8)
        user_result = evaluate_session(
            transcript_user, pid, "user_interview",
            duration=duration_user, rubric_text=rubric_text,
            selected_indicators=selected_indicators
        )
        if user_result:
            result["comm_user"] = round(float(user_result.get("comm_score", 0) or 0), 2)
            result["ct_user"] = round(float(user_result.get("ct_score", 0) or 0), 2)
            result["_detail"]["user"] = user_result
            for ind, data in user_result.get("scores", {}).items():
                result[f"{ind}_user_score"] = data.get("score", 0)

    # Evaluate client conversation session
    if transcript_client and len(str(transcript_client).strip()) > 100:
        time.sleep(8)
        client_result = evaluate_session(
            transcript_client, pid, "client_conversation",
            duration=duration_client, rubric_text=rubric_text,
            selected_indicators=selected_indicators
        )
        if client_result:
            result["comm_client"] = round(float(client_result.get("comm_score", 0) or 0), 2)
            result["ct_client"] = round(float(client_result.get("ct_score", 0) or 0), 2)
            result["_detail"]["client"] = client_result
            for ind, data in client_result.get("scores", {}).items():
                result[f"{ind}_client_score"] = data.get("score", 0)

    return result
