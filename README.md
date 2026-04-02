# RubricAI v2
### AI-Powered Student Interview Assessment Tool
Built at Northeastern University — CPS Learn Lab

---

## What Is This?

RubricAI v2 is an AI-powered tool that automatically evaluates student interview transcripts against a rubric. Instructors upload a CSV of transcripts and a rubric file, and the tool scores every student across Communication and Critical Thinking indicators — in minutes, consistently, and at scale.

What normally takes an instructor hours to evaluate manually is completed in under 3 minutes for a full class.

---

## Features

- **Dual file upload** — upload transcript CSV and rubric file together
- **AI scoring** — scores every student across 17 indicators using Claude API
- **Score colors by level** — Red (Beginning), Orange (Developing), Yellow (Applying), Green (Mastery)
- **Class Overview** — full table of all students and scores with search and filter
- **Summary and Charts** — KPI cards, bar charts by indicator, pie chart for completion status
- **Rubric Framework** — fully expandable accordion with complete level descriptors word for word
- **AI Assistant** — ask questions about student results or the rubric in natural language
- **Export** — download results as CSV or PDF report

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Backend | Python, FastAPI |
| AI Model | Claude (Anthropic API) |
| Server | Uvicorn |
| Data | CSV upload, Markdown rubric |

---

## Project Structure

```
rubricai-v2/
├── backend/
│   ├── main.py          # FastAPI server, API endpoints
│   ├── evaluator.py     # AI scoring logic
│   ├── rubric.md        # Default rubric file (gets replaced on upload)
│   ├── .env             # API keys (not committed to GitHub)
│   └── requirements.txt
├── frontend/
│   └── index.html       # Full frontend — single file
└── data/
    └── merged_sessions_nola.csv   # Sample dataset
```

---

## Setup and Running Locally

### Prerequisites
- Python 3.9+
- An Anthropic API key — get one at https://console.anthropic.com

### Step 1 — Clone the repo
```bash
git clone https://github.com/tanvisanjeev/rubricai-v2.git
cd rubricai-v2
```

### Step 2 — Set up the backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3 — Add your API key
```bash
nano .env
```
Add this line:
```
ANTHROPIC_API_KEY=your_key_here
```
Save with Ctrl+O → Enter → Ctrl+X

### Step 4 — Start the backend
```bash
uvicorn main:app --port 8000
```

### Step 5 — Start the frontend (new terminal)
```bash
cd ~/rubricai-v2/frontend
python3 -m http.server 8080
```

### Step 6 — Open in browser
```
http://localhost:8080/index.html
```

---

## How to Run an Evaluation

1. Click **Upload and Evaluate** in the sidebar
2. Upload your transcript CSV in Step 1
3. Upload your rubric file in Step 2 (optional — uses default rubric if not provided)
4. Click **Run Evaluation**
5. Results appear automatically in Class Overview when done

---

## CSV Format

Your transcript CSV should have these columns:

| Column | Description |
|---|---|
| participant_id | Unique student ID |
| simulation | Simulation name |
| completed_user | Complete or Incomplete |
| transcript_user | Full user session transcript text |
| transcript_client | Full client session transcript text |
| duration_seconds_user | Duration of user session |
| duration_seconds_client | Duration of client session |

---

## Scoring System

| Score | Level | Color |
|---|---|---|
| 1 | Beginning | 🔴 Red |
| 2 | Developing | 🟠 Orange |
| 3 | Applying | 🟡 Yellow |
| 4 | Mastery | 🟢 Green |

Students scoring below 2.0 average are flagged for instructor review.

---

---

## Roadmap

- [x] Dual file upload — CSV and rubric
- [x] AI scoring with Claude
- [x] Score colors by level
- [x] Expandable rubric accordion with full level descriptors
- [x] KPI cards, bar charts, pie chart
- [x] Export CSV and PDF
- [ ] Human vs AI score comparison tab
- [ ] Rubric chunking — send only relevant indicator per API call
- [ ] Persistent results storage across sessions
- [ ] Multi-rubric support for different courses
- [ ] Institution login and multi-cohort management

---

## Built By

Tanvi Kadam
Northeastern University — CPS Learn Lab
Active development: March–May 2026

---

## License

MIT License — free to use, modify, and distribute with attribution.
