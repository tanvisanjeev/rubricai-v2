import os
import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Indicators per session ─────────────────────────────────────────────────────
USER_INDICATORS = {
    "C1_I1": "Asks clear, open-ended questions",
    "C1_I2": "Uses follow-up questions to probe deeper into ideas or emotions",
    "C1_I3": "Demonstrates active listening (paraphrasing, clarifying, summarizing)",
    "C1_I5": "Introduces self and purpose professionally",
    "C1_I6": "Builds rapport through tone, curiosity, and responsiveness",
    "CT1_I1": "Asks clear and targeted questions to explore the client problem",
    "CT1_I3": "Evaluates relevance of information",
}

CLIENT_INDICATORS = {
    "C2_I1": "Organizes ideas logically with clear transitions",
    "C2_I2": "Connects claims to evidence during communication",
    "C2_I3": "Uses a clear, concise, professional tone",
    "CT2_I1": "Identifies relationships across data points",
    "CT2_I2": "Recognizes patterns, themes, and root causes",
    "CT2_I3": "Synthesizes evidence into insights and implications",
    "CT2_I4": "Organizes insights with clear logical structure",
    "CT3_I1": "Clearly frames the decision or direction",
    "CT3_I2": "Connects recommendations directly to evidence",
    "CT3_I4": "Provides a recommendation that is logical, feasible, and aligned with client needs",
}

SCORE_LABELS = {0: "N/A", 1: "Beginning", 2: "Developing", 3: "Applying", 4: "Mastery"}

COMM_USER   = ["C1_I1", "C1_I2", "C1_I3", "C1_I5", "C1_I6"]
CT_USER     = ["CT1_I1", "CT1_I3"]
COMM_CLIENT = ["C2_I1", "C2_I2", "C2_I3"]
CT_CLIENT   = ["CT2_I1", "CT2_I2", "CT2_I3", "CT2_I4", "CT3_I1", "CT3_I2", "CT3_I4"]


def load_rubric(rubric_text=None):
    if rubric_text:
        return rubric_text
    for fname in ["rubric.md", "rubric.txt"]:
        path = os.path.join(os.path.dirname(__file__), fname)
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()
    return None


def compute_average(scores_dict, keys):
    vals = [scores_dict[k]["score"] for k in keys
            if k in scores_dict and scores_dict[k]["score"] > 0]
    return round(sum(vals) / len(vals), 2) if vals else None


def evaluate_session(transcript, participant_id, session_type, duration=0, rubric_text=None):
    if not rubric_text:
        rubric_text = load_rubric()
    if not rubric_text:
        return {"error": "Rubric not found"}

    indicators = USER_INDICATORS if session_type == "user" else CLIENT_INDICATORS
    keys = list(indicators.keys())

    duration_note = ""
    if duration > 0:
        mins = round(duration / 60, 1)
        duration_note = f"Session duration: {mins} minutes. Normalize all quantitative thresholds proportionally to this duration."

    c1i5_note = ""
    if session_type == "user":
        c1i5_note = """
SPECIAL RULE for C1_I5:
Score ONLY the student's first [User] turn after the agent says
"You're about to begin the customer interview".
Score 0 if the student never reached this point.
"""

    ind_list = "\n".join([f"- {k}: {v}" for k, v in indicators.items()])

    example_scores = {}
    for k in keys:
        example_scores[k] = {
            "score": 2,
            "level": "Developing",
            "rationale": "2-3 sentences with specific evidence from the transcript",
            "quotes": ["direct quote from [User] turn"]
        }

    prompt = f"""You are an expert educational assessor evaluating a student in a simulation.

FULL RUBRIC:
{rubric_text}

YOUR TASK:
Score this student on ALL of the following indicators for the {session_type.upper()} session.
Evaluate each indicator INDEPENDENTLY based on its specific rubric criteria.

INDICATORS TO SCORE:
{ind_list}

{c1i5_note}

SCORING SCALE:
0 = Cannot assess (student never reached that phase)
1 = Beginning
2 = Developing
3 = Applying
4 = Mastery

{duration_note}

CRITICAL RULES:
- Score each indicator independently. Do not let one score influence another.
- Base scores ONLY on observable behaviors in the transcript, not inferred intent.
- Be consistent — same transcript must always produce same scores.
- For each indicator, find its specific criteria in the rubric and apply precisely.

STUDENT INFO:
- ID: {participant_id}
- Session: {session_type}

TRANSCRIPT:
{transcript[:6000]}

Return ONLY valid JSON — no markdown, no explanation outside JSON:
{{
  "scores": {json.dumps(example_scores, indent=2)}
}}

For each indicator:
- score: integer 0, 1, 2, 3, or 4
- level: exactly "N/A", "Beginning", "Developing", "Applying", or "Mastery"
- rationale: 2-3 sentences citing specific observable behaviors
- quotes: 1-3 short direct quotes from [User] turns only. Empty array if score is 0."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
        scores = parsed.get("scores", {})
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
                scores = parsed.get("scores", {})
            except:
                scores = {}
        else:
            scores = {}

    result = {}
    for k in keys:
        item = scores.get(k, {})
        sc = item.get("score", 0)
        if sc not in [0, 1, 2, 3, 4]:
            sc = 0
        result[k] = {
            "score":     sc,
            "level":     SCORE_LABELS[sc],
            "rationale": item.get("rationale", "Could not parse response"),
            "quotes":    item.get("quotes", []),
        }

    return result


def evaluate_participant(participant_id, simulation, transcript_user,
                         transcript_client, duration_user=0,
                         duration_client=0, rubric_text=None):
    rubric = load_rubric(rubric_text)

    result = {"participant_id": participant_id, "simulation": simulation,
              "user": None, "client": None}

    if transcript_user and len(transcript_user.strip()) > 100:
        user_scores = evaluate_session(
            transcript=transcript_user, participant_id=participant_id,
            session_type="user", duration=duration_user, rubric_text=rubric
        )
        result["user"] = {
            "scores":   user_scores,
            "comm_avg": compute_average(user_scores, COMM_USER),
            "ct_avg":   compute_average(user_scores, CT_USER),
        }

    if transcript_client and len(transcript_client.strip()) > 100:
        client_scores = evaluate_session(
            transcript=transcript_client, participant_id=participant_id,
            session_type="client", duration=duration_client, rubric_text=rubric
        )
        result["client"] = {
            "scores":   client_scores,
            "comm_avg": compute_average(client_scores, COMM_CLIENT),
            "ct_avg":   compute_average(client_scores, CT_CLIENT),
        }

    return result
