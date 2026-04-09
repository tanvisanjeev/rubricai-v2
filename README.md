# RubricAI v2
### AI-Powered Student Interview Assessment Tool
**CPS LEARN Lab · Northeastern University**
*Active development: March–May 2026 · Built by Tanvi Kadam*

---

## What Is This?

RubricAI v2 is an AI-powered tool that automatically evaluates student interview transcripts against any uploaded rubric. Instructors upload a rubric file once, upload a CSV of transcripts, and the tool scores every student across Communication and Critical Thinking indicators — with scores, rationale, and improvement feedback — in minutes.

What normally takes an instructor hours to evaluate manually is completed in under 5 minutes for a full class.

---

## Features

- **Any rubric** — upload any .md, .txt, .pdf, or .docx rubric file. Parser auto-detects clusters, indicators, and level descriptors
- **Any CSV format** — upload any transcript CSV. Columns are auto-detected or manually mapped
- **Indicator selection** — choose which indicators to evaluate using checkboxes
- **Data Setup tab** — configure course name, column names, and AI context before evaluating
- **AI scoring** — scores every student using Claude API with rationale, feedback, and quotes per indicator
- **Score colors** — Red (Beginning), Orange (Developing), Yellow (Applying), Green (Mastery)
- **Per-student downloads** — individual CSV and PDF reports with full scores, rationale, and improvement feedback
- **Download All** — full class CSV export
- **Cohort AI summary** — auto-generated paragraph summarizing class performance
- **4-tab dashboard** — Overview, User Interview, Client Conversation, Student Rankings
- **AI Assistant** — ask questions about results in natural language
- **Live clock** — US timezone switcher with calendar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Backend | Python, FastAPI |
| AI Model | Claude Sonnet (Anthropic API) |
| Server | Uvicorn |
| Data | Any CSV, Markdown/PDF/DOCX rubric |

---

## Project Structure

```
rubricai-v2/
├── backend/
│   ├── main.py          # FastAPI server — evaluation, exports, column detection
│   ├── evaluator.py     # AI scoring logic — scores, rationale, feedback per indicator
│   ├── rubric.md        # Saved rubric (replaced on upload)
│   ├── .env             # API keys (not committed)
│   └── requirements.txt
├── frontend/
│   └── index.html       # Complete single-file frontend
└── data/
    └── merged_sessions_nola.csv   # Sample dataset
```

---

## Setup

### Prerequisites
- Python 3.9+
- Anthropic API key — get one at https://console.anthropic.com

### Step 1 — Clone
```bash
git clone https://github.com/tanvisanjeev/rubricai-v2.git
cd rubricai-v2
```

### Step 2 — Backend setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3 — Add API key
```bash
nano .env
```
```
ANTHROPIC_API_KEY=your_key_here
```
Ctrl+O → Enter → Ctrl+X

### Step 4 — Start backend
```bash
uvicorn main:app --port 8000
```

### Step 5 — Start frontend (new terminal)
```bash
cd ~/rubricai-v2/frontend
python3 -m http.server 8080
```

### Step 6 — Open browser
```
http://localhost:8080/index.html
```

---

## How to Run an Evaluation

1. **Data Setup** — fill in course name and column names (optional)
2. **Rubric Framework** — upload your rubric file, select indicators
3. **Upload & Evaluate** — upload transcript CSV, click Run Evaluation
4. **Class Overview** — review scores, click any student for full details, download individual reports
5. **Summary & Charts** — view cohort dashboard and AI summary

---

## CSV Format

The tool auto-detects columns. Standard column names:

| Column | Description |
|---|---|
| participant_id | Unique student ID |
| simulation | Simulation or course name |
| completed_user | Complete or Incomplete |
| transcript_user | User interview transcript text |
| transcript_client | Client conversation transcript text |
| duration_seconds_user | Duration of user session |
| duration_seconds_client | Duration of client session |

Custom column names can be configured in Data Setup or the column mapping modal.

---

## Scoring System

| Score | Level | Color |
|---|---|---|
| 1 | Beginning | 🔴 Red |
| 2 | Developing | 🟠 Orange |
| 3 | Applying | 🟡 Yellow |
| 4 | Mastery | 🟢 Green |

Students averaging below 2.0 are flagged for instructor review.

---

## Roadmap

- [x] AI scoring with Claude
- [x] Any rubric file — dynamic parser
- [x] Any CSV format — column detection and mapping
- [x] Indicator selection checkboxes
- [x] Data Setup tab
- [x] Score colors by level
- [x] 4-tab dashboard with full indicator names
- [x] Per-student CSV and PDF downloads with feedback
- [x] Cohort AI summary
- [x] AI Assistant
- [x] Live clock with US timezone switcher
- [ ] Human vs AI score comparison tab
- [ ] Persistent results storage
- [ ] Save and reload past evaluation runs
- [ ] Canvas LMS integration
- [ ] Institution login and multi-cohort management

---

## Development Timeline

| Milestone | Date | Status |
|---|---|---|
| v1 — basic scoring | Feb 2026 | Done |
| v2 — full rebuild | Mar–Apr 2026 | Done |
| Summer cohort pilot | May–Jun 2026 | Upcoming |
| Open to institutions | After pilot | Planned |

**Active development until May 1, 2026.**

---

## Built By

**Tanvi Kadam**
AI Engineer · MS Applied Machine Intelligence
CPS LEARN Lab · Northeastern University

---

## License

MIT License — free to use, modify, and distribute with attribution.
