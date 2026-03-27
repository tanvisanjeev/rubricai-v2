# RubricAI v2

AI-powered student interview assessment platform. Automatically scores student transcripts against a research-backed rubric across Communication and Critical Thinking indicators.

---

## Overview

RubricAI v2 takes merged session CSV files containing student interview transcripts and returns structured scores for every indicator — with rationale and direct quotes from the transcript as evidence.

- 17 indicators scored across Communication and Critical Thinking
- 2 API calls per student — one for user interview session, one for client presentation
- Temperature 0 — fully deterministic, same transcript always produces same scores
- Output matches the score template format exactly
- No hardcoded data — all results come from live API evaluation

---

## Stack

- **Backend:** Python, FastAPI
- **AI:** Anthropic API
- **Frontend:** HTML, CSS, vanilla JavaScript
- **PDF Export:** ReportLab

---

## Project Structure

```
rubricai-v2/
├── backend/
│   ├── main.py           # FastAPI endpoints
│   ├── evaluator.py      # Core scoring logic and prompt engineering
│   ├── pdf_exporter.py   # PDF report generation
│   ├── rubric.md         # Full rubric — edit this to update scoring criteria
│   └── .env              # API key (not committed)
├── frontend/
│   └── index.html        # Full single-page application
└── README.md
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/tanvisanjeev/rubricai-v2.git
cd rubricai-v2
```

**2. Backend setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn anthropic python-dotenv reportlab
```

**3. Add your API key**
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

**4. Start the backend**
```bash
uvicorn main:app --port 8000
```

**5. Start the frontend**
```bash
cd ../frontend
python3 -m http.server 8080
```

**6. Open in browser**
```
http://localhost:8080/index.html
```

---

## How to Use

1. Prepare your merged sessions CSV with columns: `participant_id`, `simulation`, `transcript_user`, `transcript_client`
2. Open the platform and go to Upload and Evaluate
3. Select your CSV file and click Run Evaluation
4. Review results in Class Overview and Summary and Charts
5. Export as CSV or PDF
6. Use the AI Assistant to ask questions about the results

---

## Input Format

The platform expects a merged CSV file with the following required columns:

| Column | Description |
|--------|-------------|
| `participant_id` | Unique student identifier |
| `simulation` | Simulation name |
| `transcript_user` | Full user interview session transcript |
| `transcript_client` | Full client presentation session transcript |
| `completed_user` | Session completion status (Complete / Incomplete) |
| `duration_seconds_user` | Session duration in seconds |
| `duration_seconds_client` | Session duration in seconds |

---

## Output Format

CSV export matches the score template format:

| Column | Description |
|--------|-------------|
| `id` | Participant ID |
| `simulation` | Simulation name |
| `C1_I1_user_score` | Score 0–4 |
| `C1_I1_user_level` | N/A / Beginning / Developing / Applying / Mastery |
| `comm_user` | Average communication score — user session |
| `ct_user` | Average critical thinking score — user session |
| ... | Same pattern for all 17 indicators |

---

## Indicators Scored

**User Interview Session**
- C1_I1 — Asks clear, open-ended questions
- C1_I2 — Uses follow-up questions to probe deeper
- C1_I3 — Demonstrates active listening
- C1_I5 — Introduces self and purpose professionally
- C1_I6 — Builds rapport through tone and curiosity
- CT1_I1 — Asks targeted questions to explore the client problem
- CT1_I3 — Evaluates relevance of information

**Client Presentation Session**
- C2_I1 — Organizes ideas logically
- C2_I2 — Connects claims to evidence
- C2_I3 — Uses clear, concise, professional tone
- CT2_I1 — Identifies relationships across data points
- CT2_I2 — Recognizes patterns, themes, and root causes
- CT2_I3 — Synthesizes evidence into insights
- CT2_I4 — Organizes insights with logical structure
- CT3_I1 — Clearly frames the decision or direction
- CT3_I2 — Connects recommendations to evidence
- CT3_I4 — Provides a logical, feasible recommendation

---

## Updating the Rubric

The rubric is stored in `backend/rubric.md`. To update scoring criteria:

```bash
nano ~/rubricai-v2/backend/rubric.md
```

Save the file. The next evaluation run will automatically use the updated rubric. No code changes or server restart required.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/evaluate` | Evaluate a CSV file |
| POST | `/api/evaluate/single` | Evaluate a single participant |
| POST | `/api/export/csv` | Export results as CSV |
| POST | `/api/export/pdf` | Export results as PDF |
| POST | `/api/chat` | AI assistant query |
| GET | `/api/health` | Health check |

---

## Roadmap

- Professional Agency indicators
- Parallel processing for faster evaluation
- Manual scoring and inter-rater reliability comparison
- Result caching to avoid re-evaluating the same data
- User authentication
- Cloud deployment
- Human coder integration for validation

---

Built for CPS LEARN Lab · Northeastern University
