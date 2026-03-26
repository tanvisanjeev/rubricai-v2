from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
from datetime import datetime

ACCENT      = colors.HexColor("#2D5BE3")
LIGHT_GRAY  = colors.HexColor("#9A9A94")
MID_GRAY    = colors.HexColor("#6B6B6B")
BG_GRAY     = colors.HexColor("#F7F7F5")
BORDER      = colors.HexColor("#E4E4E0")
RED         = colors.HexColor("#C0392B")
AMBER       = colors.HexColor("#92690A")
BLUE        = colors.HexColor("#2D5BE3")
GREEN       = colors.HexColor("#1E6B3C")
WHITE       = colors.white
BLACK       = colors.HexColor("#1A1A1A")

SCORE_COLORS = {0: LIGHT_GRAY, 1: RED, 2: AMBER, 3: BLUE, 4: GREEN}
SCORE_LABELS = {0: "N/A", 1: "Beginning", 2: "Developing", 3: "Applying", 4: "Mastery"}

USER_INDS = ["C1_I1","C1_I2","C1_I3","C1_I5","C1_I6","CT1_I1","CT1_I3"]
CLIENT_INDS = ["C2_I1","C2_I2","C2_I3","CT2_I1","CT2_I2","CT2_I3","CT2_I4","CT3_I1","CT3_I2","CT3_I4"]
IND_DESC = {
    "C1_I1":"Asks clear, open-ended questions",
    "C1_I2":"Uses follow-up questions to probe deeper",
    "C1_I3":"Demonstrates active listening",
    "C1_I5":"Introduces self and purpose professionally",
    "C1_I6":"Builds rapport through tone and curiosity",
    "CT1_I1":"Asks targeted questions to explore client problem",
    "CT1_I3":"Evaluates relevance of information",
    "C2_I1":"Organizes ideas logically",
    "C2_I2":"Connects claims to evidence",
    "C2_I3":"Uses clear, concise, professional tone",
    "CT2_I1":"Identifies relationships across data points",
    "CT2_I2":"Recognizes patterns, themes, root causes",
    "CT2_I3":"Synthesizes evidence into insights",
    "CT2_I4":"Organizes insights with logical structure",
    "CT3_I1":"Clearly frames the decision or direction",
    "CT3_I2":"Connects recommendations to evidence",
    "CT3_I4":"Provides logical, feasible recommendation",
}


def _styles():
    base = getSampleStyleSheet()
    return {
        "title":  ParagraphStyle("title",  parent=base["Normal"], fontSize=18, textColor=BLACK,   spaceAfter=4,  fontName="Helvetica-Bold"),
        "meta":   ParagraphStyle("meta",   parent=base["Normal"], fontSize=9,  textColor=LIGHT_GRAY, spaceAfter=2),
        "h2":     ParagraphStyle("h2",     parent=base["Normal"], fontSize=12, textColor=BLACK,   spaceAfter=4,  fontName="Helvetica-Bold"),
        "h3":     ParagraphStyle("h3",     parent=base["Normal"], fontSize=10, textColor=ACCENT,  spaceAfter=3,  fontName="Helvetica-Bold"),
        "body":   ParagraphStyle("body",   parent=base["Normal"], fontSize=8,  textColor=MID_GRAY, spaceAfter=3, leading=13),
        "small":  ParagraphStyle("small",  parent=base["Normal"], fontSize=7,  textColor=LIGHT_GRAY, spaceAfter=2),
        "quote":  ParagraphStyle("quote",  parent=base["Normal"], fontSize=8,  textColor=MID_GRAY,
                                  leftIndent=10, fontName="Helvetica-Oblique", spaceAfter=2),
    }


def _summary_table(students, s):
    """One row per student — overview of all scores."""
    header = ["Student ID", "Simulation", "Comp.", "User Comm", "User CT", "Client Comm", "Client CT", "Status"]
    data = [header]
    for st in students:
        flagged = False
        cu, cc = st.get("comm_user"), st.get("comm_client")
        avg = (cu + cc) / 2 if (cu is not None and cc is not None) else (cu or cc)
        if avg is not None and avg < 2.0:
            flagged = True
        data.append([
            st.get("participant_id", ""),
            st.get("simulation", ""),
            "Yes" if st.get("completed") == 1 else "No",
            str(cu) if cu is not None else "N/A",
            str(st.get("ct_user")) if st.get("ct_user") is not None else "N/A",
            str(cc) if cc is not None else "N/A",
            str(st.get("ct_client")) if st.get("ct_client") is not None else "N/A",
            "Flagged" if flagged else ("Incomplete" if st.get("completed") != 1 else "Clear"),
        ])

    col_w = [1.2*inch, 1.0*inch, 0.5*inch, 0.75*inch, 0.65*inch, 0.85*inch, 0.75*inch, 0.65*inch]
    t = Table(data, colWidths=col_w)
    style = [
        ("BACKGROUND",    (0,0), (-1,0),  ACCENT),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 7.5),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [BG_GRAY, WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
        ("ALIGN",         (2,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ]
    # Color the Status column
    for i, st in enumerate(students, 1):
        cu, cc = st.get("comm_user"), st.get("comm_client")
        avg = (cu + cc) / 2 if (cu is not None and cc is not None) else (cu or cc)
        flagged = avg is not None and avg < 2.0
        col = RED if flagged else (LIGHT_GRAY if st.get("completed") != 1 else GREEN)
        style.append(("TEXTCOLOR", (7, i), (7, i), col))
        style.append(("FONTNAME",  (7, i), (7, i), "Helvetica-Bold"))

    t.setStyle(TableStyle(style))
    return t


def _indicator_table(student, session, inds):
    """Per-student indicator breakdown table."""
    detail = student.get("_detail", {})
    sess_data = detail.get(session, {}) if detail else {}
    scores = sess_data.get("scores", {}) if sess_data else {}
    suffix = "_user" if session == "user" else "_client"

    header = ["Indicator", "Description", "Score", "Level"]
    data = [header]
    for ind in inds:
        item = scores.get(ind, {})
        sc = item.get("score", student.get(f"{ind}{suffix}_score", 0) or 0)
        label = SCORE_LABELS.get(sc, "N/A")
        data.append([ind, IND_DESC.get(ind, ind), str(sc), label])

    col_w = [0.75*inch, 2.8*inch, 0.5*inch, 1.1*inch]
    t = Table(data, colWidths=col_w)
    style = [
        ("BACKGROUND",    (0,0), (-1,0),  BG_GRAY),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 7.5),
        ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
        ("ALIGN",         (2,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
    ]
    for i, ind in enumerate(inds, 1):
        item = scores.get(ind, {})
        sc = item.get("score", student.get(f"{ind}{suffix}_score", 0) or 0)
        col = SCORE_COLORS.get(sc, LIGHT_GRAY)
        style.append(("TEXTCOLOR", (2, i), (3, i), col))
        style.append(("FONTNAME",  (2, i), (3, i), "Helvetica-Bold"))

    t.setStyle(TableStyle(style))
    return t


def generate_pdf(students: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch,  bottomMargin=0.75*inch)
    s = _styles()
    story = []

    # Header
    story.append(Paragraph("RubricAI v2 — Class Evaluation Report", s["title"]))
    story.append(Paragraph(
        f"CPS LEARN Lab · Northeastern University · Generated {datetime.now().strftime('%B %d, %Y')}",
        s["meta"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))

    # Stats
    total = len(students)
    completed = sum(1 for st in students if st.get("completed") == 1)
    comm_vals = [st["comm_user"] for st in students if st.get("comm_user") is not None]
    avg_comm = round(sum(comm_vals) / len(comm_vals), 2) if comm_vals else "N/A"
    flagged_count = sum(1 for st in students if (
        st.get("comm_user") is not None and st["comm_user"] < 2.0
    ))

    stats_data = [
        ["Total Students", "Completed", "Avg User Comm", "Flagged"],
        [str(total), str(completed), str(avg_comm), str(flagged_count)]
    ]
    st_table = Table(stats_data, colWidths=[1.5*inch]*4)
    st_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  BG_GRAY),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TEXTCOLOR",     (3,1), (3,1),   RED),
        ("FONTNAME",      (0,1), (-1,1),  "Helvetica-Bold"),
    ]))
    story.append(st_table)
    story.append(Spacer(1, 16))

    # Summary table
    story.append(Paragraph("Class Overview", s["h2"]))
    story.append(_summary_table(students, s))
    story.append(Spacer(1, 20))

    # Per-student detail
    story.append(Paragraph("Individual Student Reports", s["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=10))

    for st in students:
        pid = st.get("participant_id", "Unknown")
        sim = st.get("simulation", "")
        comp = "Yes" if st.get("completed") == 1 else "No"

        story.append(Paragraph(f"{pid}  ·  {sim}", s["h3"]))
        story.append(Paragraph(
            f"Completed: {comp}  |  User Comm: {st.get('comm_user','N/A')}  |  "
            f"User CT: {st.get('ct_user','N/A')}  |  "
            f"Client Comm: {st.get('comm_client','N/A')}  |  "
            f"Client CT: {st.get('ct_client','N/A')}",
            s["body"]
        ))
        story.append(Spacer(1, 5))

        # User session indicators
        story.append(Paragraph("User Session", s["body"]))
        story.append(_indicator_table(st, "user", USER_INDS))
        story.append(Spacer(1, 6))

        # Rationale from detail if available
        detail = st.get("_detail", {})
        user_scores = detail.get("user", {}).get("scores", {}) if detail else {}
        for ind in USER_INDS:
            item = user_scores.get(ind, {})
            rationale = item.get("rationale", "")
            quotes = item.get("quotes", [])
            if rationale:
                story.append(Paragraph(f"<b>{ind}:</b> {rationale}", s["body"]))
            for q in quotes[:2]:
                story.append(Paragraph(f'"{q}"', s["quote"]))

        story.append(Spacer(1, 6))

        # Client session indicators
        story.append(Paragraph("Client Session", s["body"]))
        story.append(_indicator_table(st, "client", CLIENT_INDS))
        story.append(Spacer(1, 6))

        client_scores = detail.get("client", {}).get("scores", {}) if detail else {}
        for ind in CLIENT_INDS:
            item = client_scores.get(ind, {})
            rationale = item.get("rationale", "")
            quotes = item.get("quotes", [])
            if rationale:
                story.append(Paragraph(f"<b>{ind}:</b> {rationale}", s["body"]))
            for q in quotes[:2]:
                story.append(Paragraph(f'"{q}"', s["quote"]))

        story.append(HRFlowable(width="100%", thickness=0.3, color=BORDER, spaceAfter=8))
        story.append(Spacer(1, 4))

    doc.build(story)
    return buf.getvalue()
