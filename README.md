# RubricAI v2
### AI-Powered Student Interview Assessment Tool
**CPS LEARN Lab · Northeastern University**

---

## What Is This?

RubricAI v2 is an AI-powered tool that automatically evaluates student interview transcripts against any uploaded rubric. Instructors upload a rubric file once, then upload a CSV of transcripts, and the tool scores every student across Communication and Critical Thinking indicators — in minutes, consistently, and at scale.

What normally takes an instructor hours to evaluate manually is completed in under 5 minutes for a full class of 16 students.

---

## What's New in v2

- **Any rubric supported** — upload any markdown rubric file and the tool auto-parses clusters, indicators, and level descriptors
- **Rubric upload separate from transcript upload** — upload rubric once, it saves to disk, used for all evaluations
- **Rich home page** — problem stats, features, comparison table, AI transparency principles, roadmap
- **Dashboard charts** — 4-tab summary with KPI cards, horizontal bar charts with full indicator names, donut chart, student rankings
- **Renamed sessions** — User Interview and Client Conversation throughout
- **No hardcoded data** — everything driven by real API calls and uploaded files

---

## Features

- **Dual upload flow** — upload rubric file first, then transcript CSV
- **AI scoring** — scores every student across 17 indicators using Claude API
- **Score colors by level** — Red (Beginning), Orange (Developing), Yellow (Applying), Green (Mastery)
- **Class Overview** — full table of all students and scores with search and filter
- **Summary & Charts** — 4 tabs: Overview, User Interview, Client Conversation, Student Rankings
- **Rubric Framework** — fully expandable accordion with complete level descriptors parsed from uploaded file
- **AI Assistant** — ask questions about student results or the rubric in natural language
- **Export** — download results as CSV or PDF report

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Backend | Python, FastAPI |
| AI Model | Claude Sonnet (Anthropic API) |
| Server | Uvicorn |
| Data | CSV upload, Markdown rubric |

---

## Project Structure

```
rubricai-v2/
├── backend/
│   ├── main.py          # FastAPI server, API endpoints
│   ├── evaluator.py     # AI scoring logic
│   ├── rubric.md        # Saved rubric (replaced on upload)
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
- Anthropic API key — get one at https://console.anthropic.com

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
Add:
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

1. Click **Rubric Framework** in the sidebar
2. Upload your rubric `.md` or `.txt` file — framework populates automatically
3. Click **Upload Transcripts** in the sidebar
4. Upload your transcript CSV
5. Click **Run Evaluation**
6. Results appear automatically in Class Overview when done
7. Click **Summary & Charts** to see the full dashboard

---

## CSV Format

Your transcript CSV should have these columns:

| Column | Description |
|---|---|
| participant_id | Unique student ID |
| simulation | Simulation name |
| completed_user | Complete or Incomplete |
| transcript_user | Full user interview transcript text |
| transcript_client | Full client conversation transcript text |
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

## Roadmap

- [x] Dual file upload — rubric and transcript CSV
- [x] AI scoring with Claude
- [x] Score colors by level
- [x] Expandable rubric accordion with full level descriptors from uploaded file
- [x] KPI cards, horizontal bar charts, donut chart, student rankings
- [x] Export CSV and PDF
- [x] Rich home page with features, comparison, AI transparency
- [ ] Human vs AI score comparison tab
- [ ] Rubric chunking — send only relevant indicator per API call
- [ ] Persistent results storage across sessions
- [ ] Multi-rubric support for different courses
- [ ] Institution login and multi-cohort management

---

## Development Timeline

| Phase | Date | Status |
|---|---|---|
| v1 — Basic scoring, single indicator | Feb 2026 | Done |
| v2 — Full rubric, all indicators, dashboard | Mar–Apr 2026 | Done |
| Summer cohort pilot — 300 students | May–Jun 2026 | Upcoming |
| Open to other institutions | After pilot | Planned |

**Active development until May 1, 2026.**

---

## Built By

**Tanvi Kadam**
MS Applied Machine Intelligence · Northeastern University
CPS LEARN Lab · College of Professional Studies
Active development: March–May 2026

---

## License

MIT License — free to use, modify, and distribute with attribution.
