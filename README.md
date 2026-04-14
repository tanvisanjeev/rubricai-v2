# RubricAI v2

**AI-powered rubric-based interview assessment platform**  
CPS LEARN Lab · Northeastern University

---

## Overview

RubricAI evaluates student simulation transcripts against any rubric — delivering evidence-based scores, detailed rationale, actionable feedback, and cohort-level analytics at institutional scale.

Built for researchers and educators who need consistent, auditable, AI-assisted assessment across multi-session simulations.

---

## Features

- **Any Rubric** — Upload any markdown rubric. Clusters, indicators, and 4-level descriptors are parsed automatically. Session 1 and Session 2 indicators are detected from cluster headers
- **Any CSV** — Upload any transcript CSV. Columns are auto-detected or mapped manually
- **Multi-Session Support** — Evaluate any number of sessions in a single run. Each session's transcript is scored against its own indicator set
- **Indicator Selection** — Choose exactly which indicators to evaluate per run. All selected by default
- **Evidence-Based Scoring** — Every score includes rationale, improvement feedback, and direct transcript quotes
- **Deterministic Results** — `temperature=0` ensures consistent scores every run for the same input
- **Researcher Context** — Data Setup fields (course, cohort, simulation type, patterns to watch for) feed directly to the AI to improve scoring accuracy
- **Cohort Analytics** — KPI cards, indicator bar charts, score distribution, and AI-generated cohort summary
- **Professional Exports** — Per-participant and full-class exports in CSV and PDF
- **AI Assistant** — Full-screen natural language interface for querying evaluation results

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Backend | Python, FastAPI |
| AI Engine | Anthropic Claude API (claude-haiku-4-5) |
| PDF Export | ReportLab |
| Server | Uvicorn |

---

## Project Structure

```
rubricai-v2/
├── backend/
│   ├── main.py          # FastAPI server — all API endpoints
│   ├── evaluator.py     # AI evaluation engine
│   ├── rubric.md        # Last uploaded rubric (auto-saved)
│   └── .env             # API keys
├── frontend/
│   └── index.html       # Full single-page application
├── data/
│   ├── dataset1_healthcare.csv
│   ├── rubric_dataset1_healthcare.md
│   ├── dataset2_edtech.csv
│   └── rubric_dataset2_edtech.md
└── README.md
```

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- Anthropic API key

### Install dependencies

```bash
cd rubricai-v2/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Add your API key

Create a `.env` file in the `backend/` directory:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Running the App

**Terminal 1 — Start backend:**
```bash
cd rubricai-v2/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Start frontend:**
```bash
cd rubricai-v2/frontend
python3 -m http.server 3000
```

**Open browser:**
```
http://localhost:3000
```

---

## How to Use

### Step 1 — Data Setup
Configure course name, cohort, academic level, simulation type, participant role, number of sessions, session labels, and researcher expectations. All fields feed directly to the AI to improve scoring accuracy.

### Step 2 — Rubric Framework
Upload your rubric file (.md, .txt). The tool parses all clusters and indicators automatically. Indicators are assigned to Session 1 or Session 2 based on cluster header names. Use checkboxes to select which indicators to evaluate.

### Step 3 — Upload & Evaluate
Upload your transcript CSV. Columns are auto-detected from file headers. Click **Edit Mapping** if your column names are non-standard. Click **Run Evaluation** — takes approximately 10 seconds per participant.

### Step 4 — Class Overview
Review scores for every participant. Sort by any column. Filter by completion status. Click any participant to open the full evaluation detail — scores, rationale, feedback, and transcript quotes. Download individual CSV or PDF reports.

### Step 5 — Summary & Charts
View cohort-level performance — KPI cards, indicator bar charts, score distribution, and AI-generated cohort summary. Export the full cohort report as CSV or PDF.

### Step 6 — AI Assistant
Ask natural language questions about evaluation results — who needs most support, lowest scoring indicator, cohort average, session comparisons, and more.

---

## CSV Format

The tool auto-detects columns. Standard column names:

| Column | Description |
|---|---|
| `participant_id` | Unique participant identifier |
| `simulation` | Simulation or course name |
| `transcript_user` | Session 1 transcript text |
| `transcript_client` | Session 2 transcript text |
| `completed_user` | Completion status (Complete / Incomplete) |
| `duration_seconds_user` | Session 1 duration in seconds (optional) |
| `duration_seconds_client` | Session 2 duration in seconds (optional) |

Non-standard column names can be mapped via the Edit Mapping interface.

---

## Rubric Format

Any markdown rubric with the following structure is supported:

```markdown
#### Session 1 — Cluster Name

##### Indicator 1: Indicator Name

| Level | Criterion |
|---|---|
| Level 1 | Beginning descriptor |
| Level 2 | Developing descriptor |
| Level 3 | Applying descriptor |
| Level 4 | Mastery descriptor |

#### Session 2 — Cluster Name

##### Indicator 1: Indicator Name
...
```

Cluster headers containing **Session 1** (or `user`, `interview`) are assigned to the user interview session. Cluster headers containing **Session 2+** (or `client`, `conversation`) are assigned to the client conversation session.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/api/detect-columns` | POST | Auto-detect CSV columns |
| `/api/evaluate` | POST | Run AI evaluation |
| `/api/chat` | POST | AI Assistant chat |
| `/api/export/csv` | POST | Export class CSV |
| `/api/export/pdf` | POST | Export class PDF |
| `/api/export/cohort-pdf` | POST | Export cohort summary PDF |

---

## Test Datasets

Two synthetic datasets are included in `data/` for testing:

| Dataset | Domain | Students | Sessions |
|---|---|---|---|
| `dataset1_healthcare.csv` + `rubric_dataset1_healthcare.md` | Healthcare Operations | 5 (HC001–HC005) | 2 (User Interview + Client Conversation) |
| `dataset2_edtech.csv` + `rubric_dataset2_edtech.md` | EdTech Product Strategy | 5 (ET001–ET005) | 2 (User Interview + Client Conversation) |

Each rubric has 30 indicators — 15 per session.

---

## Roadmap

| Phase | Timeline | Features |
|---|---|---|
| Phase 1 | Feb 2026 ✅ | AI scoring · Upload flow · Export · AI Assistant |
| Phase 2 | Apr 2026 ✅ | Multi-session · Any rubric · Any CSV · Indicator selection · Cohort analytics · Professional exports |
| Phase 3 | May 2026 | Human vs AI comparison · Persistent storage · Canvas LMS integration |
| Phase 4 | Summer 2026 | Multi-institution · Subscription · REST API |

---

## Built By

**Tanvi Kadam**  
AI Engineer · MS Applied Machine Intelligence · Northeastern University

**CPS LEARN Lab**  
College of Professional Studies · Northeastern University

---

## License

Research use only. Not for commercial distribution without permission.  
© 2026 CPS LEARN Lab · Northeastern University
