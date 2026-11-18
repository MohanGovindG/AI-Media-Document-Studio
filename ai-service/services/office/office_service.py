import io
import json
import csv
import time
from typing import Dict, Any, Tuple, List, Optional
try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    from pptx import Presentation
    from pptx.util import Inches as PptInches, Pt as PptPt
except ImportError:
    Presentation = None

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RlImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    pass

try:
    import pymupdf as fitz
except ImportError:
    import fitz

class OfficeConversionService:
    """
    Production-grade Office document conversion engine:
    DOCX ↔ PDF, DOCX ↔ TXT, DOCX ↔ HTML, DOCX ↔ Markdown,
    XLSX ↔ PDF, XLSX ↔ CSV, XLSX ↔ JSON, XLSX ↔ HTML,
    PPTX ↔ PDF, PPTX ↔ Images, Images ↔ PPTX.
    """

    # --- WORD (DOCX) CONVERSIONS ---

    @classmethod
    def docx_to_pdf(cls, docx_bytes: bytes) -> bytes:
        """Converts DOCX text & tables into a clean PDF using ReportLab."""
        doc = docx.Document(io.BytesIO(docx_bytes))
        out_buf = io.BytesIO()
        pdf = SimpleDocTemplate(out_buf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        story = []
        for p in doc.paragraphs:
            if not p.text.strip():
                story.append(Spacer(1, 10))
                continue

            style_name = 'Normal'
            if p.style.name.startswith('Heading 1'):
                style_name = 'Heading1'
            elif p.style.name.startswith('Heading 2'):
                style_name = 'Heading2'
            elif p.style.name.startswith('Heading 3'):
                style_name = 'Heading3'

            # Clean XML entities
            clean_text = p.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(clean_text, styles[style_name]))
            story.append(Spacer(1, 6))

        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = [Paragraph(cell.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), styles['Normal']) for cell in row.cells]
                table_data.append(row_data)

            if table_data:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1'))
                ]))
                story.append(t)
                story.append(Spacer(1, 12))

        pdf.build(story)
        return out_buf.getvalue()

    @classmethod
    def pdf_to_docx(cls, pdf_bytes: bytes) -> bytes:
        """Reconstructs DOCX document from PDF text and layout blocks."""
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        doc = docx.Document()

        for page in pdf_doc:
            blocks = page.get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                if text:
                    p = doc.add_paragraph(text)
                    p.paragraph_format.space_after = Pt(6)

        out_buf = io.BytesIO()
        doc.save(out_buf)
        pdf_doc.close()
        return out_buf.getvalue()

    @classmethod
    def docx_to_txt(cls, docx_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(docx_bytes))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n\n".join(paragraphs)

    @classmethod
    def txt_to_docx(cls, text_content: str) -> bytes:
        doc = docx.Document()
        for line in text_content.splitlines():
            doc.add_paragraph(line)
        out_buf = io.BytesIO()
        doc.save(out_buf)
        return out_buf.getvalue()

    @classmethod
    def docx_to_markdown(cls, docx_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(docx_bytes))
        md_lines = []
        for p in doc.paragraphs:
            if not p.text.strip():
                continue
            if p.style.name.startswith("Heading 1"):
                md_lines.append(f"# {p.text}")
            elif p.style.name.startswith("Heading 2"):
                md_lines.append(f"## {p.text}")
            elif p.style.name.startswith("Heading 3"):
                md_lines.append(f"### {p.text}")
            else:
                md_lines.append(p.text)
        return "\n\n".join(md_lines)

    @classmethod
    def markdown_to_docx(cls, md_text: str) -> bytes:
        doc = docx.Document()
        for line in md_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("### "):
                doc.add_heading(stripped[4:], level=3)
            elif stripped.startswith("## "):
                doc.add_heading(stripped[3:], level=2)
            elif stripped.startswith("# "):
                doc.add_heading(stripped[2:], level=1)
            else:
                doc.add_paragraph(line)
        out_buf = io.BytesIO()
        doc.save(out_buf)
        return out_buf.getvalue()

    # --- EXCEL (XLSX) CONVERSIONS ---

    @classmethod
    def xlsx_to_csv(cls, xlsx_bytes: bytes) -> str:
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
        sheet = wb.active
        out = io.StringIO()
        writer = csv.writer(out)
        for row in sheet.iter_rows(values_only=True):
            writer.writerow([v if v is not None else "" for v in row])
        return out.getvalue()

    @classmethod
    def csv_to_xlsx(cls, csv_text: str) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        reader = csv.reader(io.StringIO(csv_text))
        for row in reader:
            ws.append(row)
        out_buf = io.BytesIO()
        wb.save(out_buf)
        return out_buf.getvalue()

    @classmethod
    def xlsx_to_json(cls, xlsx_bytes: bytes) -> str:
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return "[]"
        headers = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
        data = []
        for r in rows[1:]:
            row_dict = {}
            for i, val in enumerate(r):
                header_key = headers[i] if i < len(headers) else f"col_{i}"
                row_dict[header_key] = val
            data.append(row_dict)
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def json_to_xlsx(cls, json_text: str) -> bytes:
        data = json.loads(json_text)
        wb = openpyxl.Workbook()
        ws = wb.active
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            headers = list(data[0].keys())
            ws.append(headers)
            for item in data:
                ws.append([item.get(h, "") for h in headers])
        out_buf = io.BytesIO()
        wb.save(out_buf)
        return out_buf.getvalue()

    @classmethod
    def xlsx_to_pdf(cls, xlsx_bytes: bytes) -> bytes:
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))

        out_buf = io.BytesIO()
        pdf = SimpleDocTemplate(out_buf, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()

        table_data = []
        for r in rows[:100]: # Cap table preview rows
            table_data.append([Paragraph(str(v) if v is not None else "", styles['Normal']) for v in r])

        if not table_data:
            table_data = [[Paragraph("Empty Sheet", styles['Normal'])]]

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8'))
        ]))

        pdf.build([t])
        return out_buf.getvalue()

    # --- POWERPOINT (PPTX) CONVERSIONS ---

    @classmethod
    def pptx_to_pdf(cls, pptx_bytes: bytes) -> bytes:
        """Converts PPTX slide texts and shapes into a structured PDF document."""
        prs = Presentation(io.BytesIO(pptx_bytes))
        out_buf = io.BytesIO()
        pdf = SimpleDocTemplate(out_buf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        story = []

        for i, slide in enumerate(prs.slides):
            story.append(Paragraph(f"<b>Slide {i + 1}</b>", styles['Heading2']))
            story.append(Spacer(1, 8))
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if paragraph.text.strip():
                            story.append(Paragraph(paragraph.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), styles['Normal']))
                            story.append(Spacer(1, 4))
            story.append(Spacer(1, 16))

        pdf.build(story)
        return out_buf.getvalue()

    @classmethod
    def images_to_pptx(cls, image_bytes_list: List[bytes]) -> bytes:
        """Creates PPTX presentation with one slide per image."""
        prs = Presentation()
        # Set 16:9 widescreen dimensions
        prs.slide_width = PptInches(13.333)
        prs.slide_height = PptInches(7.5)
        blank_slide_layout = prs.slide_layouts[6]

        for img_bytes in image_bytes_list:
            slide = prs.slides.add_slide(blank_slide_layout)
            img_stream = io.BytesIO(img_bytes)
            slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)

        out_buf = io.BytesIO()
        prs.save(out_buf)
        return out_buf.getvalue()
