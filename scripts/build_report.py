#!/usr/bin/env python3
"""Render a security intelligence brief PDF from a report JSON file.

Usage: python build_report.py report.json output.pdf
Requires: reportlab  (pip install reportlab --break-system-packages)

report.json schema (all string fields are plain text; omit/null anything unknown):
{
  "title": "Security Intelligence Brief",
  "date": "2026-06-12",
  "window": "Last 30 days",
  "audience_note": "Monthly CISO staff meeting",          // optional
  "prepared_for": "Leadership",                           // optional
  "executive_summary": "Plain-language summary...",
  "recommendations": ["Patch X within 7 days", "..."],
  "methodology_note": "Data from NVD, CISA KEV ...",      // optional
  "products": [
    {
      "vendor": "Apache", "product": "Tomcat", "version": "9.0.85",
      "risk": "High",                       // Critical | High | Medium | Low
      "risk_rationale": "One sentence naming the deciding factor.",
      "latest_version": "9.0.118",
      "eol": "2027-03-31",                  // date, "No" or "EOL since YYYY-MM-DD"
      "version_status": "33 patch releases behind; cycle supported until 2027-03-31.",
      "kev_count": 1,
      "cve_total": 39,                      // total found (table may show fewer)
      "cves": [
        {"id": "CVE-2025-24813", "cvss": 9.8, "severity": "CRITICAL",
         "kev": true, "kev_due": "2025-04-22",            // kev_due optional
         "summary": "Path equivalence RCE ...", "fixed_in": "9.0.99"}
      ],
      "advisories": [{"title": "...", "date": "2026-05-01", "url": "https://..."}],
      "news": [{"title": "...", "source": "BleepingComputer", "date": "2026-06-02",
                "summary": "one line", "url": "https://..."}],
      "sources": ["https://...", "..."]
    }
  ]
}
"""
import json, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

INK = colors.HexColor("#1a1f2b")
MUTED = colors.HexColor("#5a6372")
ACCENT = colors.HexColor("#b03a2e")
LIGHT = colors.HexColor("#f4f5f7")
RISK_COLORS = {"Critical": colors.HexColor("#b03a2e"), "High": colors.HexColor("#d68910"),
               "Medium": colors.HexColor("#b7950b"), "Low": colors.HexColor("#1e8449")}

ss = getSampleStyleSheet()
def st(name, **kw):
    base = kw.pop("base", "Normal")
    kw.setdefault("textColor", INK)
    return ParagraphStyle(name, parent=ss[base], **kw)

S = {
    "title":  st("t",  base="Title", fontSize=26, leading=31, textColor=INK, spaceAfter=4),
    "subtle": st("sb", fontSize=10.5, textColor=MUTED, spaceAfter=2),
    "h1":     st("h1", base="Heading1", fontSize=16, textColor=INK, spaceBefore=14, spaceAfter=6),
    "h2":     st("h2", base="Heading2", fontSize=12.5, textColor=INK, spaceBefore=10, spaceAfter=4),
    "body":   st("bd", fontSize=10, leading=14.5, spaceAfter=6),
    "cell":   st("cl", fontSize=8.5, leading=11),
    "cellb":  st("cb", fontSize=8.5, leading=11, fontName="Helvetica-Bold"),
    "rec":    st("rc", fontSize=10.5, leading=15, leftIndent=14, spaceAfter=5),
    "src":    st("sr", fontSize=7.5, leading=10, textColor=MUTED),
}

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if s else ""

def risk_chip(risk):
    c = RISK_COLORS.get(risk, MUTED)
    t = Table([[Paragraph(f'<font color="white"><b>{esc(risk).upper()}</b></font>', S["cell"])]],
              colWidths=[0.95 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), c), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("ROUNDEDCORNERS", [4, 4, 4, 4])]))
    return t

def grid(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 6),
             ("RIGHTPADDING", (0, 0), (-1, -1), 6),
             ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#dcdfe4"))]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), INK),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])]
    t.setStyle(TableStyle(style))
    return t

def hdr_footer(canvas, doc, title):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.5 * inch, f"{title}  ·  CONFIDENTIAL — INTERNAL USE")
    canvas.drawRightString(LETTER[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()

def build(data, out_path):
    doc = BaseDocTemplate(out_path, pagesize=LETTER, topMargin=0.75 * inch, bottomMargin=0.8 * inch,
                          leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                          title=data.get("title", "Security Intelligence Brief"))
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame],
                          onPage=lambda c, d: hdr_footer(c, d, data.get("title", "Security Brief")))])
    W = doc.width
    el = []

    # ---- Cover / exec summary page ----
    el.append(Paragraph(esc(data.get("title", "Security Intelligence Brief")), S["title"]))
    meta = f"{esc(data.get('date',''))}  ·  Window: {esc(data.get('window',''))}"
    if data.get("prepared_for"): meta += f"  ·  Prepared for: {esc(data['prepared_for'])}"
    el.append(Paragraph(meta, S["subtle"]))
    if data.get("audience_note"):
        el.append(Paragraph(esc(data["audience_note"]), S["subtle"]))
    el.append(Spacer(1, 6)); el.append(HRFlowable(width="100%", color=ACCENT, thickness=2)); el.append(Spacer(1, 10))

    el.append(Paragraph("Executive Summary", S["h1"]))
    el.append(Paragraph(esc(data.get("executive_summary", "")), S["body"]))

    # Risk overview table
    el.append(Paragraph("Risk Overview", S["h1"]))
    rows = [[Paragraph(f"<b>{h}</b>", S["cell"]) for h in
             ["Product", "Version", "Risk", "KEV", "CVEs found", "Why"]]]
    for p in data.get("products", []):
        rows.append([
            Paragraph(f"{esc(p.get('vendor',''))} {esc(p.get('product',''))}", S["cellb"]),
            Paragraph(esc(p.get("version") or "all"), S["cell"]),
            risk_chip(p.get("risk", "—")),
            Paragraph(str(p.get("kev_count", 0)), S["cell"]),
            Paragraph(str(p.get("cve_total", len(p.get("cves", [])))), S["cell"]),
            Paragraph(esc(p.get("risk_rationale", "")), S["cell"]),
        ])
    el.append(grid(rows, [1.5 * inch, 0.75 * inch, 1.05 * inch, 0.5 * inch, 0.75 * inch, W - 4.55 * inch]))

    if data.get("recommendations"):
        el.append(Paragraph("Recommended Actions", S["h1"]))
        for i, r in enumerate(data["recommendations"], 1):
            el.append(Paragraph(f"<b>{i}.</b>  {esc(r)}", S["rec"]))

    # ---- Per-product sections ----
    for p in data.get("products", []):
        el.append(PageBreak())
        name = f"{esc(p.get('vendor',''))} {esc(p.get('product',''))}"
        ver = esc(p.get("version") or "all supported versions")
        el.append(Paragraph(f"{name} <font color='#5a6372' size='11'>({ver})</font>", S["h1"]))
        head = Table([[risk_chip(p.get("risk", "—")),
                       Paragraph(esc(p.get("risk_rationale", "")), S["body"])]],
                     colWidths=[1.05 * inch, W - 1.05 * inch])
        head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("LEFTPADDING", (0, 0), (0, 0), 0)]))
        el.append(head)

        el.append(Paragraph("Version &amp; Patch Status", S["h2"]))
        vs = [["Running version", ver], ["Latest version", esc(p.get("latest_version", "unknown"))],
              ["End of life", esc(p.get("eol", "unknown"))], ["Status", esc(p.get("version_status", ""))]]
        el.append(grid([[Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])] for a, b in vs],
                       [1.6 * inch, W - 1.6 * inch], header=False))

        cves = p.get("cves", [])
        total = p.get("cve_total", len(cves))
        el.append(Paragraph(f"Vulnerabilities ({total} found{', top shown' if total > len(cves) else ''})", S["h2"]))
        if cves:
            rows = [[Paragraph(f"<b>{h}</b>", S["cell"]) for h in
                     ["CVE", "CVSS", "Severity", "KEV", "Summary", "Fixed in"]]]
            for c in sorted(cves, key=lambda c: (not c.get("kev"), -(c.get("cvss") or 0))):
                kev = "⚠ YES" + (f"<br/>due {esc(c['kev_due'])}" if c.get("kev_due") else "") if c.get("kev") else "—"
                rows.append([Paragraph(esc(c.get("id", "")), S["cellb"]),
                             Paragraph(str(c.get("cvss", "—")), S["cell"]),
                             Paragraph(esc(c.get("severity", "—")), S["cell"]),
                             Paragraph(kev, S["cellb" if c.get("kev") else "cell"]),
                             Paragraph(esc(c.get("summary", "")), S["cell"]),
                             Paragraph(esc(c.get("fixed_in", "—")), S["cell"])])
            el.append(grid(rows, [0.95 * inch, 0.45 * inch, 0.65 * inch, 0.7 * inch, W - 3.55 * inch, 0.8 * inch]))
        else:
            el.append(Paragraph("No matching CVEs found in the selected window/version.", S["body"]))

        if p.get("advisories"):
            el.append(Paragraph("Vendor Advisories", S["h2"]))
            for a in p["advisories"]:
                el.append(Paragraph(
                    f"• <b>{esc(a.get('title',''))}</b> ({esc(a.get('date',''))}) — "
                    f"<font color='#5a6372'>{esc(a.get('url',''))}</font>", S["body"]))
        if p.get("news"):
            el.append(Paragraph("Security News", S["h2"]))
            for n in p["news"]:
                line = f"• <b>{esc(n.get('title',''))}</b> — {esc(n.get('source',''))}, {esc(n.get('date',''))}"
                if n.get("summary"): line += f". {esc(n['summary'])}"
                el.append(Paragraph(line, S["body"]))
        if p.get("sources"):
            el.append(Paragraph("Sources", S["h2"]))
            for s_ in p["sources"]:
                el.append(Paragraph(esc(s_), S["src"]))

    if data.get("methodology_note"):
        el.append(Spacer(1, 14)); el.append(HRFlowable(width="100%", color=colors.HexColor("#dcdfe4")))
        el.append(Paragraph(f"Methodology: {esc(data['methodology_note'])}", S["src"]))

    doc.build(el)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python build_report.py report.json output.pdf")
    with open(sys.argv[1]) as f:
        build(json.load(f), sys.argv[2])
