from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io

# ── Colour palette
PURPLE      = colors.HexColor("#6366f1")
DARK_BG     = colors.HexColor("#111827")
MID_GRAY    = colors.HexColor("#374151")
LIGHT_GRAY  = colors.HexColor("#9ca3af")
GREEN       = colors.HexColor("#10b981")
AMBER       = colors.HexColor("#f59e0b")
RED         = colors.HexColor("#ef4444")
BLUE        = colors.HexColor("#3b82f6")
WHITE       = colors.white
BLACK       = colors.black

LEVEL_COLORS = {1: RED, 2: AMBER, 3: BLUE, 4: GREEN}

def _styles():
    base = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",    parent=base["Normal"], fontSize=20, textColor=PURPLE,    spaceAfter=4,  fontName="Helvetica-Bold"),
        "h2":       ParagraphStyle("h2",        parent=base["Normal"], fontSize=13, textColor=BLACK,     spaceAfter=4,  fontName="Helvetica-Bold"),
        "h3":       ParagraphStyle("h3",        parent=base["Normal"], fontSize=11, textColor=PURPLE,    spaceAfter=3,  fontName="Helvetica-Bold"),
        "body":     ParagraphStyle("body",      parent=base["Normal"], fontSize=9,  textColor=colors.HexColor("#374151"), spaceAfter=3, leading=14),
        "small":    ParagraphStyle("small",     parent=base["Normal"], fontSize=8,  textColor=LIGHT_GRAY, spaceAfter=2),
        "quote":    ParagraphStyle("quote",     parent=base["Normal"], fontSize=8,  textColor=colors.HexColor("#4b5563"),
                                   leftIndent=12, borderPad=4, backColor=colors.HexColor("#f9fafb"),
                                   fontName="Helvetica-Oblique", spaceAfter=3),
        "center":   ParagraphStyle("center",    parent=base["Normal"], fontSize=9,  alignment=TA_CENTER),
    }

def _score_table(students):
    """Summary table — one row per student."""
    data = [["Student", "Communication", "Critical Thinking", "Prof. Agency", "Overall"]]
    for s in students:
        d = s.get("scores", {}).get("domains", {})
        data.append([
            f"Student {s['student_id']}",
            str(d.get("Communication", {}).get("score") or "N/A"),
            str(d.get("Critical Thinking", {}).get("score") or "N/A"),
            str(d.get("Professional Agency", {}).get("score") or "N/A"),
            str(s.get("scores", {}).get("overall") or "N/A"),
        ])

    t = Table(data, colWidths=[1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.0*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  PURPLE),
        ("TEXTCOLOR",    (0,0), (-1,0),  WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f9fafb"), WHITE]),
        ("GRID",         (0,0), (-1,-1), 0.4, colors.HexColor("#e5e7eb")),
        ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    return t

def generate_pdf(students: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch,  bottomMargin=0.75*inch)
    s = _styles()
    story = []

    # ── Cover / header
    story.append(Paragraph("RubricAI — Evaluation Report", s["title"]))
    story.append(Paragraph("CPS LEARN Lab · Northeastern University · Indicator 1: Asks clear, open-ended questions", s["small"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=10))

    # ── Summary table
    story.append(Paragraph("Class Summary", s["h2"]))
    story.append(_score_table(students))
    story.append(Spacer(1, 14))

    # ── Per-student pages
    for s_data in students:
        sid   = s_data.get("student_id", "?")
        evals = s_data.get("results", [])
        scores = s_data.get("scores", {})
        overall = scores.get("overall", "N/A")

        story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Student {sid}  —  Overall Score: {overall} / 4.0", s["h2"]))

        if not evals:
            story.append(Paragraph("No evaluations available.", s["body"]))
            continue

        for ev in evals:
            lvl   = ev.get("level", 1)
            conf  = ev.get("confidence", 0)
            color = LEVEL_COLORS.get(lvl, BLACK)
            sim   = ev.get("simulation", "?")

            story.append(Spacer(1, 6))
            story.append(Paragraph(f"Simulation {sim}", s["h3"]))

            # Level + metrics row
            meta = [
                ["Level", "Confidence", "Open-Ended Qs", "Closed Qs", "Strategic Phrasing"],
                [str(lvl), f"{round(conf*100)}%",
                 str(ev.get("open_ended_count", 0)),
                 str(ev.get("closed_count", 0)),
                 str(ev.get("strategic_phrasing_count", 0))]
            ]
            mt = Table(meta, colWidths=[1.0*inch]*5)
            mt.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#f3f4f6")),
                ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",     (0,0), (-1,-1), 8),
                ("TEXTCOLOR",    (0,1), (0,1),  color),
                ("FONTNAME",     (0,1), (0,1),  "Helvetica-Bold"),
                ("ALIGN",        (0,0), (-1,-1), "CENTER"),
                ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
                ("TOPPADDING",   (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ]))
            story.append(mt)
            story.append(Spacer(1, 5))

            # Justification
            story.append(Paragraph(f"<b>Justification:</b> {ev.get('justification','')}", s["body"]))

            # Evidence quotes
            examples = ev.get("open_ended_examples", [])
            if examples:
                story.append(Paragraph("<b>Evidence — Open-Ended Questions Found:</b>", s["body"]))
                for q in examples[:4]:
                    story.append(Paragraph(f'"{q}"', s["quote"]))

            # Strengths / Improvements
            sw = ev.get("strengths", "")
            im = ev.get("improvements", "")
            if sw or im:
                rows = [["Strengths", "Areas for Improvement"],
                        [sw or "—", im or "—"]]
                ft = Table(rows, colWidths=[3.5*inch, 3.5*inch])
                ft.setStyle(TableStyle([
                    ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#f3f4f6")),
                    ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",     (0,0), (-1,-1), 8),
                    ("VALIGN",       (0,0), (-1,-1), "TOP"),
                    ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
                    ("TOPPADDING",   (0,0), (-1,-1), 5),
                    ("BOTTOMPADDING",(0,0), (-1,-1), 5),
                    ("LEFTPADDING",  (0,0), (-1,-1), 6),
                ]))
                story.append(ft)

            story.append(Spacer(1, 8))

    doc.build(story)
    return buf.getvalue()
