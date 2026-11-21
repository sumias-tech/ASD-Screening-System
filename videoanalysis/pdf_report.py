# pdf_report.py

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from datetime import datetime
import os
 
 
# ── Colour palette (mirrors the web UI) ──────────────────────────────────────
C_NAVY    = colors.HexColor("#0f1923")
C_ACCENT  = colors.HexColor("#1d6fa4")
C_ACCENT2 = colors.HexColor("#0ea5e9")
C_MID     = colors.HexColor("#4a5568")
C_DIM     = colors.HexColor("#94a3b8")
C_BORDER  = colors.HexColor("#e2e8f0")
C_BG      = colors.HexColor("#f4f6f9")
C_WHITE   = colors.white
 
C_LOW_BG  = colors.HexColor("#dcfce7")
C_LOW_FG  = colors.HexColor("#0f7a55")
C_MOD_BG  = colors.HexColor("#fef9c3")
C_MOD_FG  = colors.HexColor("#92580a")
C_HIGH_BG = colors.HexColor("#fee2e2")
C_HIGH_FG = colors.HexColor("#b91c1c")
C_UNK_BG  = colors.HexColor("#f1f5f9")
C_UNK_FG  = C_DIM
 
 
def _risk_colors(risk):
    """Return (background, foreground) colors for a given risk label."""
    r = risk.lower()
    if r == "low":      return C_LOW_BG,  C_LOW_FG
    if r == "moderate": return C_MOD_BG,  C_MOD_FG
    if r == "high":     return C_HIGH_BG, C_HIGH_FG
    return C_UNK_BG, C_UNK_FG
 
 
def _risk_description(risk):
    r = risk.lower()
    if r == "low":
        return "Behavioral indicators are within the typical range. No immediate clinical concern."
    if r == "moderate":
        return "Some behavioral indicators require closer attention. A follow-up session is recommended."
    if r == "high":
        return "Significant behavioral indicators detected. Clinical review is strongly advised."
    return "Insufficient data to classify risk level."
 
 
def generate_pdf(result):
 
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    file_path = os.path.join(static_dir, "report.pdf")
 
    # ── Document setup ────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
 
    W = doc.width  # usable page width
 
    # ── Style helpers ─────────────────────────────────────────────────────
    def style(name, **kw):
        return ParagraphStyle(name, **kw)
 
    s_report_tag = style("ReportTag",
        fontSize=8, textColor=C_ACCENT, fontName="Helvetica-Bold", spaceAfter=4)
 
    s_h1 = style("H1",
        fontSize=18, textColor=C_NAVY, fontName="Helvetica-Bold",
        spaceAfter=2, leading=22)
 
    s_sub = style("Sub",
        fontSize=9, textColor=C_DIM, fontName="Helvetica", spaceAfter=0)
 
    s_section = style("Section",
        fontSize=8.5, textColor=C_DIM, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6, letterSpacing=0.8)
 
    s_metric_label = style("MetricLabel",
        fontSize=7.5, textColor=C_DIM, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=2)
 
    s_metric_value = style("MetricValue",
        fontSize=22, textColor=C_NAVY, fontName="Helvetica-Bold",
        alignment=TA_CENTER, leading=26)
 
    s_metric_text = style("MetricText",
        fontSize=10, textColor=C_NAVY, fontName="Helvetica-Bold",
        alignment=TA_CENTER, leading=14)

    s_score_label = style("ScoreLabel",
        fontSize=8, textColor=C_DIM, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=4)

    s_score_big = style("ScoreBig",
        fontSize=30, textColor=C_NAVY, fontName="Helvetica-Bold",
        alignment=TA_CENTER, leading=34)
 
    s_footer = style("Footer",
        fontSize=7.5, textColor=C_DIM, fontName="Helvetica", alignment=TA_CENTER)
 
    # ── Story ─────────────────────────────────────────────────────────────
    story = []
 
    # ── HEADER BAR ────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("ASD BEHAVIORAL FRAMEWORK · ROBOT-ENHANCED THERAPY",
                  style("HdrTag", fontSize=7.5, textColor=C_WHITE,
                        fontName="Helvetica-Bold", alignment=TA_LEFT)),
        Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}",
                  style("HdrDate", fontSize=7.5,
                        textColor=colors.HexColor("#a8d4ef"),
                        fontName="Helvetica", alignment=TA_RIGHT)),
    ]]
 
    header_tbl = Table(header_data, colWidths=[W * 0.65, W * 0.35])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_ACCENT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (0, -1),  12),
        ("RIGHTPADDING",  (-1, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 16))
 
    # ── TITLE BLOCK ───────────────────────────────────────────────────────
    story.append(Paragraph("BEHAVIORAL ASSESSMENT REPORT", s_report_tag))
    story.append(Paragraph("Autism Spectrum Disorder<br/>Behavioral Analysis", s_h1))
    story.append(Paragraph(
        f"Session analyzed using MediaPipe pose detection · "
        f"{result.get('frames', 0)} frames processed",
        s_sub))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=14))
 
    # ── SCORE + RISK HERO ─────────────────────────────────────────────────
    risk        = result.get("risk", "Unknown")
    risk_bg, risk_fg = _risk_colors(risk)
 
    score_cell = [
        [Paragraph("OVERALL SUMMARY", s_score_label)],
        [Paragraph(result.get("overall_summary", "A descriptive behavioral summary is not available."),
                   style("ScoreSummary", fontSize=10, textColor=C_NAVY,
                         fontName="Helvetica", alignment=TA_CENTER, leading=14))],
    ]
 
    risk_cell = [
        [Paragraph("RISK CLASSIFICATION", s_score_label)],
        [Paragraph(f"{risk} Risk",
                   style("RiskVal", fontSize=18, fontName="Helvetica-Bold",
                         textColor=risk_fg, alignment=TA_CENTER))],
        [Paragraph(_risk_description(risk),
                   style("RiskDesc", fontSize=8.5, textColor=C_MID,
                         fontName="Helvetica", alignment=TA_CENTER, leading=13))],
    ]
 
    # ✅ FIXED: removed dead `score_tbl = Table(Table(...).wrap(0,0) and ...)` line
    #    that was computed but never used in the story.
    hero = Table(
        [[Table(score_cell, colWidths=[W * 0.34]),
          Table(risk_cell,  colWidths=[W * 0.58])]],
        colWidths=[W * 0.38, W * 0.62]
    )
    hero.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0),  C_BG),
        ("BACKGROUND",    (1, 0), (1, 0),  risk_bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 1, C_BORDER),
        ("LINEAFTER",     (0, 0), (0, -1),  1, C_BORDER),
    ]))
    story.append(hero)
    story.append(Spacer(1, 18))
 
    # ── METRICS ROW ───────────────────────────────────────────────────────
    story.append(Paragraph("BEHAVIOR METRICS", s_section))
 
    # ✅ FIXED: third metric label + description updated to reflect wrist
    #    velocity / repetitive movement (not body posture / shoulder symmetry)
    metrics = [
        ("FACE DIRECTION",
         result.get("face_summary", "No face direction summary available."),
         "Your child’s face orientation during the session."),
 
        ("HEAD POSE",
         result.get("head_summary", "No head pose summary available."),
         "A description of head movement and stability."),
 
        ("REPETITIVE BEHAVIOR",
         result.get("repetitive_summary", "No repetitive behavior summary available."),
         "A parent-friendly summary of observed repetitive actions."),
    ]
 
    col = W / 3 - 4
 
    def metric_cell(label, value, desc):
        return [
            [Paragraph(label, s_metric_label)],
            [Paragraph(str(value), s_metric_text)],
            [Paragraph(desc, style("MDesc", fontSize=7.5, textColor=C_DIM,
                                   fontName="Helvetica", alignment=TA_CENTER, leading=11))],
        ]
 
    metrics_data = [[Table(metric_cell(*m), colWidths=[col]) for m in metrics]]
 
    metrics_tbl = Table(metrics_data, colWidths=[col + 4] * 3)
    metrics_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_WHITE),
        ("BOX",           (0, 0), (0, 0),   1, C_BORDER),
        ("BOX",           (1, 0), (1, 0),   1, C_BORDER),
        ("BOX",           (2, 0), (2, 0),   1, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(metrics_tbl)
    story.append(Spacer(1, 18))
 
    # ── GRAPH ─────────────────────────────────────────────────────────────
    graph_path = os.path.join("static", "graph.png")
 
    if os.path.exists(graph_path):
        story.append(Paragraph("FRAME-BY-FRAME ANALYSIS", s_section))
 
        img     = Image(graph_path, width=W, height=W * 0.42)
        img.hAlign = "LEFT"
 
        img_tbl = Table([[img]], colWidths=[W])
        img_tbl.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 1, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("BACKGROUND",    (0, 0), (-1, -1), C_WHITE),
        ]))
        story.append(img_tbl)
        story.append(Spacer(1, 18))
 
    # ── DISCLAIMER + FOOTER ───────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=8))
    story.append(Paragraph(
        "This report is generated automatically by the ASD Behavioral Framework and is "
        "intended as a supportive screening tool only. It does not constitute a clinical "
        "diagnosis. All results should be reviewed by a qualified healthcare professional.",
        style("Disclaimer", fontSize=7.5, textColor=C_DIM,
              fontName="Helvetica", alignment=TA_CENTER, leading=12)
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"ASD Behavioral Framework · Robot-Enhanced Therapy System · "
        f"Report generated {datetime.now().strftime('%d %B %Y')}",
        s_footer
    ))
 
    # ── Build ─────────────────────────────────────────────────────────────
    doc.build(story)
 
    return "report.pdf"