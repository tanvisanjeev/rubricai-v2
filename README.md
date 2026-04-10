# RubricAI v2

**AI-powered rubric-based interview assessment platform**  
CPS LEARN Lab · Northeastern University

---

## Overview

RubricAI evaluates student interview transcripts against any rubric — delivering evidence-based scores, detailed rationale, actionable feedback, and cohort-level analytics at institutional scale.

Built for researchers and educators who need consistent, auditable, AI-assisted assessment at scale.

---

## Features

- **Any Rubric** — Upload any markdown rubric. Clusters, indicators, and 4-level descriptors are parsed automatically
- **Any CSV** — Upload any transcript CSV. Columns are auto-detected or mapped manually
- **Indicator Selection** — Choose exactly which indicators to evaluate per run. All selected by default
- **Evidence-Based Scoring** — Every score includes rationale, improvement feedback, and direct transcript quotes
- **Deterministic Results** — `temperature=0` ensures consistent scores every run for the same input
- **Researcher Context** — Data Setup fields feed course, cohort, simulation, and evaluation context directly to the AI
- **Cohort Analytics** — KPI cards, indicator bar charts, score distribution, participant rankings, AI-generated cohort summary
- **Professional Exports** — Per-participant and full-class exports in CSV and PDF — academic, print-ready format
- **AI Assistant** — Natural language queries over evaluation results

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Backend | Python, FastAPI |
| AI Engine | Anthropic Claude API (claude-sonnet-4) |
| PDF Export | ReportLab |
| Server | Uvicorn |

---

## Project Structure

```
rubricai-v2/
├── backend/
│   ├── main.py          # FastAPI server — all API endpoints
│   ├── evaluator.py     # AI evaluation engine
│   └── rubric.md        # Last uploaded rubric (auto-saved)
├── frontend/
│   └── index.html       # Full single-page application
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
pip install fastapi uvicorn anthropic reportlab python-multipart
```

### Add your API key

Open `backend/evaluator.py` and `backend/main.py` and replace the API key:

```python
return anthropic.Anthropic(api_key="sk-ant-your-key-here")
```

---

## Running the App

**Terminal 1 — Start backend:**
```bash
cd rubricai-v2/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
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
Configure course name, cohort, academic level, simulation type, participant role, evaluation purpose, and researcher expectations. All fields are fed directly to the AI to improve scoring accuracy.

### Step 2 — Rubric Framework
Upload your rubric file (.md, .txt, .pdf, .docx). The tool parses all clusters and indicators automatically. Use checkboxes to select which indicators to evaluate — all selected by default.

### Step 3 — Upload & Evaluate
Upload your transcript CSV. Columns are auto-detected from file headers. Click Edit Mapping if your column names are non-standard. Click Run Evaluation — takes 5–15 minutes depending on cohort size.

### Step 4 — Class Overview
Review scores for every participant across all evaluated indicators. Sort by any column. Filter by simulation or completion status. Click any participant ID to open the full evaluation detail — scores, rationale, feedback, and transcript evidence. Download individual CSV or PDF reports.

### Step 5 — Summary & Charts
View cohort-level performance — KPI cards, indicator bar charts, score distribution, participant rankings, and AI-generated cohort summary. Export the full class report.

### Step 6 — AI Assistant
Ask natural language questions about evaluation results — who needs most support, lowest indicator, cohort average, session comparisons, and more.

---

## CSV Format

The tool auto-detects columns. Standard column names:

| Column | Description |
|---|---|
| `participant_id` | Unique participant identifier |
| `simulation` | Simulation or course name |
| `transcript_user` | Session 1 (User Interview) transcript text |
| `transcript_client` | Session 2 (Client Conversation) transcript text |
| `completed_user` | Completion status (Complete/Incomplete) |
| `duration_seconds_user` | Session 1 duration in seconds (optional) |
| `duration_seconds_client` | Session 2 duration in seconds (optional) |

Non-standard column names can be mapped via the Edit Mapping interface.

---

## Rubric Format

Any markdown rubric with the following structure is supported:

```markdown
#### Cluster Name

##### Indicator 1: Indicator Name

| Level | Criterion |
|---|---|
| Level 1 | Beginning descriptor |
| Level 2 | Developing descriptor |
| Level 3 | Applying descriptor |
| Level 4 | Mastery descriptor |
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/api/evaluate` | POST | Run AI evaluation |
| `/api/chat` | POST | AI Assistant chat |
| `/api/export/csv` | POST | Export class CSV |
| `/api/export/pdf` | POST | Export class PDF |
| `/api/detect-columns` | POST | Auto-detect CSV columns |

---

## Roadmap

| Phase | Timeline | Features |
|---|---|---|
| Phase 1 | Feb 2026 ✅ | AI scoring · Upload flow · Export · AI Assistant |
| Phase 2 | Apr 2026 ✅ | Any rubric · Any CSV · Indicator selection · Cohort summary · Professional exports |
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
