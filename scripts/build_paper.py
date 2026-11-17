"""Typeset the research paper from Markdown and existing aggregate reports.

Install paper/requirements.txt in a separate environment. This script neither
imports the study package nor trains models or reads row-level trip data.
"""
from __future__ import annotations

import csv
import html
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from markdown_it import MarkdownIt
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SOURCE = PAPER / "the-tipping-point.md"
FIGURES = PAPER / "figures"
NAVY = "183746"
TEAL = "007E87"
GRAY = "52616B"
DATE = "17 November 2026"
PARSER = MarkdownIt("commonmark").enable("table")


def rows(name):
    with (ROOT / "reports" / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def figures():
    """Render manuscript-specific figures from the already saved aggregates."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.labelcolor": f"#{NAVY}", "text.color": f"#{NAVY}",
        "axes.titleweight": "bold", "savefig.facecolor": "white",
    })
    fig, ax = plt.subplots(figsize=(10.2, 2.65))
    ax.set(xlim=(0, 10.2), ylim=(0, 2.65))
    ax.axis("off")
    cohorts = [("May 2026", "FIT", "train", "56.17% positive"),
               ("June 2026", "SELECT", "validation", "59.54% positive"),
               ("July 2026", "TEST ONCE", "test", "58.45% positive")]
    for i, (month, action, split, prevalence) in enumerate(cohorts):
        x = 0.15 + i * 3.4
        audit = rows(f"tables/cleaning_{split}.csv")
        n = int(audit[-1]["remaining"])
        ax.add_patch(FancyBboxPatch((x, 0.5), 3.1, 1.9,
                     boxstyle="round,pad=0.02,rounding_size=0.08",
                     facecolor="#EFF5F6", edgecolor=f"#{TEAL}", linewidth=1.2))
        ax.text(x + 0.16, 2.1, action, fontsize=10, color=f"#{TEAL}", weight="bold")
        ax.text(x + 0.16, 1.68, month, fontsize=16, weight="bold")
        ax.text(x + 0.16, 1.25, f"{n:,} eligible trips", fontsize=12)
        ax.text(x + 0.16, 0.86, prevalence, fontsize=10)
        if i < 2:
            ax.annotate("", xy=(x+3.38, 1.46), xytext=(x+3.13, 1.46),
                        arrowprops={"arrowstyle": "->", "color": f"#{GRAY}", "lw": 1.4})
    ax.text(5.1, 0.12, "Preprocessing and model fit on May only; no May–June refit.",
            ha="center", fontsize=10)
    fig.tight_layout(pad=0.4)
    save_figure(fig, "study-design")

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.65), gridspec_kw={"width_ratios": [1.6, 1]})
    for ax, table, labels, title in [
        (axes[0], rows("tables/rates_fare_band.csv"),
         ["(0, 10]", "(10, 20]", "(20, 40]", "(40, 80]", ">80"], "A. Meter fare (USD)"),
        (axes[1], rows("tables/rates_airport_trip.csv"),
         ["Non-airport", "Airport"], "B. Airport status"),
    ]:
        values = [100 * float(r["rate"]) for r in table]
        errors = [[100*(float(r["rate"])-float(r["lower_95"])) for r in table],
                  [100*(float(r["upper_95"])-float(r["rate"])) for r in table]]
        ax.bar(range(len(table)), values, color=f"#{TEAL}", width=0.57,
               yerr=errors, capsize=3, error_kw={"lw": 1, "color": f"#{NAVY}"})
        ax.axhline(56.16670257625658, color=f"#{GRAY}", ls="--", lw=1)
        ax.set_xticks(range(len(table)), labels)
        ax.set_ylim(0, 93)
        ax.set_title(title, loc="left", fontsize=11, pad=12)
        ax.set_ylabel("Recorded positive rate (%)")
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#E4E8EB", lw=0.6)
        for i, (value, row) in enumerate(zip(values, table)):
            ax.text(i, value + 5, f"n={int(row['n']):,}", ha="center", fontsize=8)
    fig.tight_layout(pad=1.1)
    save_figure(fig, "may-rates")


def save_figure(fig, name):
    fig.savefig(FIGURES / f"{name}.png", dpi=240, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def blocks():
    tokens = PARSER.parse(SOURCE.read_text(encoding="utf-8"))
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "heading_open":
            result.append(("heading", int(token.tag[1]), tokens[i+1].children))
            i += 3
        elif token.type == "paragraph_open":
            children = tokens[i+1].children or []
            if len(children) == 1 and children[0].type == "image":
                result.append(("image", children[0].attrGet("src"), children[0].content))
            else:
                result.append(("paragraph", children, None))
            i += 3
        elif token.type == "fence":
            result.append(("code", token.content.rstrip(), None))
            i += 1
        elif token.type == "table_open":
            table, current = [], []
            i += 1
            while tokens[i].type != "table_close":
                if tokens[i].type == "tr_open":
                    current = []
                elif tokens[i].type == "inline":
                    current.append(tokens[i].children or [])
                elif tokens[i].type == "tr_close":
                    table.append(current)
                i += 1
            result.append(("table", table, None))
            i += 1
        else:
            raise ValueError(f"Unsupported manuscript block: {token.type}")
    return result


def plain(children):
    return "".join(" " if t.type in {"softbreak", "hardbreak"} else t.content
                   for t in children if t.type in {"text", "code_inline", "softbreak", "hardbreak"})


def rich(children):
    parts = []
    for token in children:
        if token.type == "text":
            parts.append(html.escape(token.content))
        elif token.type == "code_inline":
            parts.append(f'<font name="Mono" size="8.4">{html.escape(token.content)}</font>')
        elif token.type in {"strong_open", "strong_close", "em_open", "em_close"}:
            parts.append({"strong_open": "<b>", "strong_close": "</b>",
                          "em_open": "<i>", "em_close": "</i>"}[token.type])
        elif token.type == "link_open":
            parts.append(f'<link href="{html.escape(token.attrGet("href"), quote=True)}" color="#{TEAL}">')
        elif token.type == "link_close":
            parts.append("</link>")
        elif token.type == "hardbreak":
            parts.append("<br/>")
        elif token.type == "softbreak":
            parts.append(" ")
        else:
            raise ValueError(f"Unsupported inline: {token.type}")
    return "".join(parts)


def register_fonts():
    directory = Path(matplotlib.get_data_path()) / "fonts/ttf"
    for family, stem in [("Body", "DejaVuSerif"), ("Sans", "DejaVuSans"), ("Mono", "DejaVuSansMono")]:
        italic = "Italic" if family == "Body" else "Oblique"
        for suffix, file_suffix in [("", ""), ("-Bold", "-Bold"),
                                    ("-Italic", f"-{italic}"), ("-BoldItalic", f"-Bold{italic}")]:
            pdfmetrics.registerFont(TTFont(family+suffix, str(directory/f"{stem}{file_suffix}.ttf")))
        pdfmetrics.registerFontFamily(family, normal=family, bold=family+"-Bold",
                                      italic=family+"-Italic", boldItalic=family+"-BoldItalic")


class PaperPDF(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"H2", "H3"}:
            title = flowable.getPlainText()
            key = "section-" + re.sub(r"[^A-Za-z0-9]+", "-", title)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0 if flowable.style.name == "H2" else 1)


def build_pdf(content):
    register_fonts()
    body = ParagraphStyle("Body", fontName="Body", fontSize=10.2, leading=14.5,
                          spaceAfter=7, alignment=TA_JUSTIFY, textColor=colors.HexColor("#202C33"))
    styles = {
        "body": body,
        "title": ParagraphStyle("Title", parent=body, fontName="Sans-Bold", fontSize=29,
                                leading=34, textColor=colors.HexColor(f"#{NAVY}"), spaceAfter=13,
                                alignment=TA_LEFT),
        "subtitle": ParagraphStyle("Subtitle", parent=body, fontName="Sans", fontSize=11.8,
                                   leading=16, alignment=TA_LEFT, spaceAfter=10),
        "meta": ParagraphStyle("Meta", parent=body, fontName="Sans", fontSize=9,
                               leading=13, alignment=TA_LEFT, spaceAfter=9),
        "h2": ParagraphStyle("H2", parent=body, fontName="Sans-Bold", fontSize=14,
                             leading=18, spaceBefore=15, spaceAfter=8, keepWithNext=True,
                             alignment=TA_LEFT, textColor=colors.HexColor(f"#{NAVY}")),
        "h3": ParagraphStyle("H3", parent=body, fontName="Sans-Bold", fontSize=11,
                             leading=15, spaceBefore=10, spaceAfter=6, keepWithNext=True,
                             alignment=TA_LEFT, textColor=colors.HexColor(f"#{NAVY}")),
        "caption": ParagraphStyle("Caption", parent=body, fontName="Sans", fontSize=8.4,
                                  leading=11.4, alignment=TA_LEFT, textColor=colors.HexColor(f"#{GRAY}")),
        "table_caption": ParagraphStyle("TableCaption", parent=body, fontName="Sans", fontSize=9,
                                        leading=12, alignment=TA_LEFT, keepWithNext=True),
        "cell": ParagraphStyle("Cell", fontName="Sans", fontSize=8, leading=10.7,
                               textColor=colors.HexColor("#202C33")),
        "cell_head": ParagraphStyle("CellHead", fontName="Sans-Bold", fontSize=8, leading=10.7,
                                    textColor=colors.HexColor(f"#{NAVY}")),
        "code": ParagraphStyle("Code", fontName="Mono", fontSize=7.8, leading=11.5,
                               spaceBefore=4, spaceAfter=8, backColor=colors.HexColor("#F2F5F6"),
                               borderPadding=7, alignment=TA_LEFT),
    }
    doc = PaperPDF(str(PAPER / "the-tipping-point.pdf"), pagesize=A4,
                   leftMargin=49, rightMargin=49, topMargin=47, bottomMargin=46,
                   title="The Tipping Point: Predicting Recorded Generous Card Tips",
                   author="Team D", subject="Temporal classification study of NYC taxi card tips")
    story = []
    skipped = set()
    for index, (kind, value, extra) in enumerate(content):
        if index in skipped:
            continue
        if kind == "heading":
            story.append(Paragraph(rich(extra), styles["title" if value == 1 else f"h{value}"]))
        elif kind == "paragraph":
            text = plain(value)
            style = styles["body"]
            if text.startswith("Predicting Recorded Generous"):
                style = styles["subtitle"]
            elif text.startswith("Team D ·"):
                style = styles["meta"]
            elif text.startswith("Table "):
                style = styles["table_caption"]
            elif text.startswith(("Figure ", "Source:", "Source for Tables")):
                style = styles["caption"]
            story.append(Paragraph(rich(value), style))
        elif kind == "code":
            markup = "<br/>".join(html.escape(line).replace(" ", "&#160;") for line in value.splitlines())
            story.append(Paragraph(markup, styles["code"]))
        elif kind == "image":
            from PIL import Image as PILImage
            path = (PAPER / value).resolve()
            with PILImage.open(path) as img:
                width, height = img.size
            flow = Image(str(path), width=doc.width, height=doc.width*height/width)
            group = [flow, Spacer(1, 4)]
            if index + 1 < len(content):
                following = content[index+1]
                if following[0] == "paragraph" and plain(following[1]).startswith("Figure "):
                    group.append(Paragraph(rich(following[1]), styles["caption"]))
                    skipped.add(index+1)
            story.extend([Spacer(1, 7), KeepTogether(group)])
        elif kind == "table":
            count = len(value[0])
            if count >= 5:
                widths = [doc.width*0.29] + [doc.width*0.71/(count-1)]*(count-1)
            elif count == 3:
                widths = [doc.width*0.26, doc.width*0.39, doc.width*0.35]
            else:
                widths = [doc.width*0.4] + [doc.width*0.6/(count-1)]*(count-1)
            cells = [[Paragraph(rich(cell), styles["cell_head" if r == 0 else "cell"])
                      for cell in row] for r, row in enumerate(value)]
            table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFEAED")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F8")]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor(f"#{TEAL}")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#C5D1D6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([table, Spacer(1, 8)])

    def page(canvas, document):
        canvas.saveState()
        canvas.setFont("Sans", 7.5)
        canvas.setFillColor(colors.HexColor(f"#{GRAY}"))
        if document.page > 1:
            canvas.drawString(49, A4[1]-27, "THE TIPPING POINT  |  TEAM D")
            canvas.setStrokeColor(colors.HexColor("#CFD9DD"))
            canvas.line(49, A4[1]-33, A4[0]-49, A4[1]-33)
        canvas.drawString(49, 25, f"Research paper  |  {DATE}")
        canvas.drawRightString(A4[0]-49, 25, str(document.page))
        canvas.restoreState()
    doc.build(story, onFirstPage=page, onLaterPages=page)


def word_inline(paragraph, children):
    bold = italic = False
    link = None
    for token in children:
        if token.type in {"strong_open", "strong_close"}:
            bold = token.type == "strong_open"
        elif token.type in {"em_open", "em_close"}:
            italic = token.type == "em_open"
        elif token.type == "link_open":
            link = token.attrGet("href")
        elif token.type == "link_close":
            link = None
        elif token.type in {"text", "code_inline", "softbreak", "hardbreak"}:
            text = " " if token.type == "softbreak" else "\n" if token.type == "hardbreak" else token.content
            run = paragraph.add_run(text)
            run.bold, run.italic = bold, italic
            if token.type == "code_inline":
                run.font.name = "Consolas"
                run.font.size = Pt(9)
            if link:
                run.font.color.rgb = RGBColor.from_string(TEAL)
                hyperlink = OxmlElement("w:hyperlink")
                hyperlink.set(qn("r:id"), paragraph.part.relate_to(link, RT.HYPERLINK, is_external=True))
                hyperlink.append(run._r)
                paragraph._p.append(hyperlink)
        else:
            raise ValueError(f"Unsupported Word inline: {token.type}")


def build_docx(content):
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.2677), Inches(11.6929)
    section.top_margin = section.bottom_margin = Inches(0.75)
    section.left_margin = section.right_margin = Inches(0.72)
    normal = document.styles["Normal"]
    normal.font.name = "Cambria"
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.widow_control = True
    for name in ["Title", "Heading 1", "Heading 2"]:
        style = document.styles[name]
        style.font.name = "Calibri"
        style.font.color.rgb = RGBColor.from_string(NAVY)
        style.paragraph_format.keep_with_next = True
    document.styles["Title"].font.size = Pt(30)
    document.styles["Heading 1"].font.size = Pt(15)
    document.styles["Heading 2"].font.size = Pt(12)
    caption = document.styles["Caption"]
    caption.font.name = "Calibri"
    caption.font.size = Pt(9)
    caption.font.color.rgb = RGBColor.from_string(GRAY)
    header = section.header.paragraphs[0]
    header.text = "THE TIPPING POINT  |  TEAM D"
    header.style = "Caption"
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run(f"{DATE}  |  ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    document.core_properties.title = "The Tipping Point"
    document.core_properties.subject = "Predicting recorded generous card tips in NYC yellow taxis"
    document.core_properties.author = "Team D"
    document.core_properties.keywords = "taxi, tipping, temporal validation, machine learning"
    for kind, value, extra in content:
        if kind == "heading":
            paragraph = document.add_paragraph(style="Title" if value == 1 else f"Heading {value-1}")
            word_inline(paragraph, extra)
        elif kind == "paragraph":
            text = plain(value)
            is_caption = text.startswith(("Figure ", "Source:", "Source for Tables"))
            paragraph = document.add_paragraph(style="Caption" if is_caption else "Normal")
            word_inline(paragraph, value)
            if text.startswith("Predicting Recorded Generous"):
                paragraph.style = "Subtitle"
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif text.startswith("Team D ·"):
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif text.startswith("Table "):
                paragraph.paragraph_format.keep_with_next = True
            elif not is_caption:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif kind == "image":
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
            shape = paragraph.add_run().add_picture(str((PAPER/value).resolve()), width=Inches(6.8))
            shape._inline.docPr.set("descr", extra)
        elif kind == "code":
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.keep_together = True
            paragraph.paragraph_format.line_spacing = 1.0
            run = paragraph.add_run(value)
            run.font.name, run.font.size = "Consolas", Pt(8.5)
        elif kind == "table":
            count = len(value[0])
            table = document.add_table(rows=0, cols=count)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = "Light Shading Accent 1"
            table.autofit = False
            fractions = ([0.29] + [0.71/(count-1)]*(count-1) if count >= 5
                         else [0.26, 0.39, 0.35] if count == 3
                         else [0.4] + [0.6/(count-1)]*(count-1))
            for col, fraction in zip(table.columns, fractions):
                col.width = Inches(6.8*fraction)
            for index, row in enumerate(value):
                cells = table.add_row().cells
                for cell, children, fraction in zip(cells, row, fractions):
                    cell.width = Inches(6.8*fraction)
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                    paragraph = cell.paragraphs[0]
                    paragraph.paragraph_format.line_spacing = 1.0
                    paragraph.paragraph_format.space_after = Pt(4)
                    word_inline(paragraph, children)
                    for run in paragraph.runs:
                        run.font.name, run.font.size = "Calibri", Pt(9)
                        if index == 0:
                            run.bold = True
                    if index == 0:
                        shade = OxmlElement("w:shd")
                        shade.set(qn("w:fill"), "DFEAED")
                        cell._tc.get_or_add_tcPr().append(shade)
                properties = table.rows[index]._tr.get_or_add_trPr()
                properties.append(OxmlElement("w:cantSplit"))
                if index == 0:
                    properties.append(OxmlElement("w:tblHeader"))
            document.add_paragraph().paragraph_format.space_after = Pt(2)
    document.save(PAPER / "the-tipping-point.docx")


def main():
    figures()
    content = blocks()
    build_pdf(content)
    build_docx(content)
    words = len(SOURCE.read_text(encoding="utf-8").split())
    print(f"Built PDF and Word from {SOURCE.relative_to(ROOT)} ({words:,} whitespace-separated words).")


if __name__ == "__main__":
    main()
