import os
import json
import time
import anthropic

# ── CLIENT ────────────────────────────────────────────────────
def get_client():
    return anthropic.Anthropic(api_key="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")

# ── LOAD RUBRIC ───────────────────────────────────────────────
def load_rubric(rubric_text=None):
    if rubric_text:
        return rubric_text
    rubric_path = os.path.join(os.path.dirname(__file__), "rubric.md")
    if os.path.exists(rubric_path):
        with open(rubric_path, "r") as f:
            return f.read()
    return ""

# ── BUILD CONTEXT FROM DATA SETUP ────────────────────────────
def build_context(setup_data=None):
    if not setup_data:
        return ""
    parts = []
    if setup_data.get("course"):
        parts.append(f"Course/Program: {setup_data['course']}")
    if setup_data.get("academic_level"):
        parts.append(f"Academic Level: {setup_data['academic_level']}")
    if setup_data.get("institution"):
        parts.append(f"Institution: {setup_data['institution']}")
    if setup_data.get("cohort"):
        parts.append(f"Cohort/Semester: {setup_data['cohort']}")
    if setup_data.get("simulation_type"):
        parts.append(f"Simulation Type: {setup_data['simulation_type']}")
    if setup_data.get("participant_role"):
        parts.append(f"Participant Role: {setup_data['participant_role']}")
    if setup_data.get("session_number"):
        parts.append(f"Session: {setup_data['session_number']}")
    if setup_data.get("eval_purpose"):
        parts.append(f"Evaluation Purpose: {setup_data['eval_purpose']}")
    if setup_data.get("expected_level"):
        parts.append(f"Expected Performance Level: {setup_data['expected_level']}")
    if setup_data.get("language_expectation"):
        parts.append(f"Language/Tone Expectation: {setup_data['language_expectation']}")
    if setup_data.get("researcher_looking_for"):
        parts.append(f"Researcher is looking for: {setup_data['researcher_looking_for']}")
    if setup_data.get("strong_performance"):
        parts.append(f"Strong performance looks like: {setup_data['strong_performance']}")
    if setup_data.get("red_flags"):
        parts.append(f"Red flags to watch for: {setup_data['red_flags']}")
    if setup_data.get("cohort_notes"):
        parts.append(f"Additional cohort context: {setup_data['cohort_notes']}")
    return "\n".join(parts)

# ── DETERMINE FLAGS FROM SCORES ───────────────────────────────
def determine_flags(scores_dict):
    """
    AI-driven flagging based on rubric evidence — no arbitrary threshold.
    Flag if: 2+ indicators at Level 1, OR overall avg below 2.0, OR no scores at all.
    """
    if not scores_dict:
        return True, "No scores recorded — session may be incomplete or transcript too short."
    score_values = [v.get("score", 0) for v in scores_dict.values() if v.get("score")]
    if not score_values:
        return True, "No valid scores found."
    level1_count = sum(1 for s in score_values if s == 1)
    avg = sum(score_values) / len(score_values)
    reasons = []
    if level1_count >= 2:
        reasons.append(f"{level1_count} indicators scored at Beginning (Level 1)")
    if avg < 2.0:
        reasons.append(f"Overall average {avg:.2f} below developing threshold")
    if reasons:
        return True, "; ".join(reasons)
    return False, ""

# ── EVALUATE SESSION ──────────────────────────────────────────
def evaluate_session(
    transcript, participant_id, session_type,
    duration=0, rubric_text=None,
    selected_indicators=None, setup_data=None
):
    if not rubric_text:
        rubric_text = load_rubric()

    rubric_section = rubric_text
    transcript_section = str(transcript)

    # Default fallback indicators
    if session_type == "user_interview":
        default_indicators = ["C1_I1", "C1_I2", "C1_I3", "C1_I5", "C1_I6", "CT1_I1", "CT1_I3"]
    else:
        default_indicators = ["C2_I1", "C2_I2", "C2_I3", "CT2_I1", "CT2_I2", "CT2_I3", "CT2_I4", "CT3_I1", "CT3_I2", "CT3_I4"]

    # ── USE SELECTED INDICATORS DIRECTLY ──
    if selected_indicators and len(selected_indicators) > 0:
        indicators_to_use = list(selected_indicators)
    else:
        indicators_to_use = default_indicators

    if not indicators_to_use:
        print(f"  No indicators to evaluate for {participant_id} [{session_type}]")
        return None

    ind_list = ", ".join(indicators_to_use)
    context_block = build_context(setup_data)

    print(f"  Evaluating {participant_id} [{session_type}] — {len(indicators_to_use)} indicators")

    prompt = f"""You are an expert rubric-based educational assessor working for a university research lab.
Your evaluations must be evidence-based, consistent, and academically rigorous.

PARTICIPANT ID: {participant_id}
SESSION TYPE: {session_type}
DURATION: {duration} seconds

{"EVALUATION CONTEXT:" if context_block else ""}
{context_block}

RUBRIC (score strictly against these level descriptors):
{rubric_section}

TRANSCRIPT TO EVALUATE:
{transcript_section}

YOUR TASK:
Evaluate ONLY these indicators: {ind_list}

For EACH indicator ID above, provide:
- score: integer 1, 2, 3, or 4 (must match rubric level descriptors exactly)
- rationale: 2-3 sentences explaining exactly why this score — reference specific rubric criteria and specific evidence from transcript
- feedback: 1-2 sentences of specific, actionable improvement advice tied to reaching the next level
- quotes: list of up to 2 direct quotes from transcript supporting the score (empty list [] if none found)

Also provide:
- comm_score: average of ALL indicator scores (float, 1 decimal)
- ct_score: 0.0 if no critical thinking indicators present, else average of CT indicator scores
- summary: 2-3 sentence analytical summary of overall performance — be specific, reference patterns

CRITICAL RULES:
- Use EXACT indicator IDs from this list as JSON keys: {ind_list}
- Score ONLY based on rubric criteria — not general impression
- temperature=0 means be deterministic and consistent
- If transcript is too short to evaluate an indicator, score it 1 and note it in rationale
- Never invent quotes — only use text actually present in transcript

Return ONLY valid JSON, no markdown, no code blocks, no extra text:
{{
  "scores": {{
    "INDICATOR_ID": {{
      "score": 2,
      "rationale": "specific explanation referencing rubric criteria and transcript evidence",
      "feedback": "specific actionable advice for reaching next level",
      "quotes": ["exact quote from transcript"]
    }}
  }},
  "comm_score": 2.3,
  "ct_score": 1.8,
  "summary": "analytical performance summary"
}}"""

    try:
        client = get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        print(f"    Raw response length: {len(text)} chars")

        # Strip markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(text)
        score_count = len(parsed.get("scores", {}))
        print(f"    ✓ {score_count} indicators scored successfully")
        return parsed

    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parse error for {participant_id} [{session_type}]: {e}")
        print(f"    Response preview: {text[:300] if 'text' in dir() else 'no response'}")
        return None
    except Exception as e:
        print(f"    ✗ Error evaluating {participant_id} [{session_type}]: {e}")
        return None

# ── FLEXIBLE COLUMN EXTRACTION ────────────────────────────────
def get_col(row, *keys, default=""):
    for k in keys:
        if k in row and row[k]:
            return row[k]
    row_lower = {str(k).lower().strip(): v for k, v in row.items()}
    for k in keys:
        if str(k).lower() in row_lower and row_lower[str(k).lower()]:
            return row_lower[str(k).lower()]
    return default

# ── EVALUATE PARTICIPANT ──────────────────────────────────────
def evaluate_participant(row, rubric_text=None, selected_indicators=None, setup_data=None):
    pid = get_col(row, "participant_id", "student_id", "id", "student", "name", "participant")
    simulation = get_col(row, "simulation", "sim", "course", "assignment", "session_name", "scenario")
    transcript_user = get_col(
        row, "transcript_user", "user_transcript", "interview_transcript",
        "transcript_a", "script_a", "user_session", "interview"
    )
    transcript_client = get_col(
        row, "transcript_client", "client_transcript", "client_conversation",
        "transcript_b", "script_b", "client_session", "client"
    )
    duration_user = get_col(row, "duration_seconds_user", "duration_user", "user_duration", default=0)
    duration_client = get_col(row, "duration_seconds_client", "duration_client", "client_duration", default=0)
    completed_user = get_col(row, "completed_user", "completed", "status", default="Complete")

    print(f"\nParticipant: {pid} | Simulation: {simulation}")
    print(f"  User transcript: {len(str(transcript_user))} chars | Client transcript: {len(str(transcript_client))} chars")
    print(f"  Selected indicators: {selected_indicators}")

    result = {
        "participant_id": str(pid) if pid else "unknown",
        "simulation": str(simulation) if simulation else "unknown",
        "completed": 1 if str(completed_user).lower() in ["complete", "yes", "1", "true", "y"] else 0,
        "comm_user": None, "ct_user": None,
        "comm_client": None, "ct_client": None,
        "_detail": {}
    }

    # ── USER INTERVIEW ──
    if transcript_user and len(str(transcript_user).strip()) > 50:
        time.sleep(5)
        user_result = evaluate_session(
            transcript_user, pid, "user_interview",
            duration=duration_user,
            rubric_text=rubric_text,
            selected_indicators=selected_indicators,
            setup_data=setup_data
        )
        if user_result:
            result["comm_user"] = round(float(user_result.get("comm_score") or 0), 2)
            result["ct_user"] = round(float(user_result.get("ct_score") or 0), 2)
            result["_detail"]["user"] = user_result
            for ind, data in user_result.get("scores", {}).items():
                result[f"{ind}_user_score"] = data.get("score", 0)
        else:
            print(f"  ✗ No result for {pid} user_interview")
    else:
        print(f"  Skipping user transcript — too short or empty")

    # ── CLIENT CONVERSATION ──
    if transcript_client and len(str(transcript_client).strip()) > 50:
        time.sleep(5)
        client_result = evaluate_session(
            transcript_client, pid, "client_conversation",
            duration=duration_client,
            rubric_text=rubric_text,
            selected_indicators=selected_indicators,
            setup_data=setup_data
        )
        if client_result:
            result["comm_client"] = round(float(client_result.get("comm_score") or 0), 2)
            result["ct_client"] = round(float(client_result.get("ct_score") or 0), 2)
            result["_detail"]["client"] = client_result
            for ind, data in client_result.get("scores", {}).items():
                result[f"{ind}_client_score"] = data.get("score", 0)
        else:
            print(f"  ✗ No result for {pid} client_conversation")
    else:
        print(f"  Skipping client transcript — too short or empty")

    return result
