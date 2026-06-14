from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable
import os
import re

# ── Palette ────────────────────────────────────────────────────────────────
DARK       = colors.HexColor("#1A1A2E")
ACCENT     = colors.HexColor("#E94560")
ACCENT2    = colors.HexColor("#0F3460")
LIGHT_BG   = colors.HexColor("#F5F7FA")
MID_GRAY   = colors.HexColor("#8892A4")
BORDER     = colors.HexColor("#D1D9E6")
WHITE      = colors.white
TEXT       = colors.HexColor("#2D3748")
WARN_BG    = colors.HexColor("#FFF5F5")
WARN_BORDER= colors.HexColor("#FC8181")
TIP_BG     = colors.HexColor("#F0FFF4")
TIP_BORDER = colors.HexColor("#68D391")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

ACCENTS = {
    "Guida Utente": colors.HexColor("#38A169"),
    "Guida Amministratore": ACCENT,
    "Guida SuperAdmin": colors.HexColor("#805AD5"),
}

APP_NAME = "ValBelluna Motorsport"

# ── Stili ─────────────────────────────────────────────────────────────────
def make_styles(accent=ACCENT):
    s = {}

    s['cover_title'] = ParagraphStyle(
        'cover_title', fontName='Helvetica-Bold',
        fontSize=32, leading=40, textColor=WHITE,
        alignment=TA_CENTER, spaceAfter=6
    )
    s['cover_subtitle'] = ParagraphStyle(
        'cover_subtitle', fontName='Helvetica',
        fontSize=14, leading=20, textColor=colors.HexColor("#CBD5E0"),
        alignment=TA_CENTER, spaceAfter=4
    )
    s['cover_role'] = ParagraphStyle(
        'cover_role', fontName='Helvetica-Bold',
        fontSize=11, leading=16, textColor=accent,
        alignment=TA_CENTER, spaceAfter=2,
    )
    s['toc_title'] = ParagraphStyle(
        'toc_title', fontName='Helvetica-Bold',
        fontSize=13, leading=18, textColor=DARK,
        spaceAfter=8, spaceBefore=6
    )
    s['toc_item'] = ParagraphStyle(
        'toc_item', fontName='Helvetica',
        fontSize=10, leading=16, textColor=TEXT,
        leftIndent=8
    )
    s['section_title'] = ParagraphStyle(
        'section_title', fontName='Helvetica-Bold',
        fontSize=15, leading=20, textColor=WHITE,
        spaceBefore=14, spaceAfter=10
    )
    s['subsection'] = ParagraphStyle(
        'subsection', fontName='Helvetica-Bold',
        fontSize=11, leading=16, textColor=ACCENT2,
        spaceBefore=10, spaceAfter=4,
    )
    s['body'] = ParagraphStyle(
        'body', fontName='Helvetica',
        fontSize=10, leading=16, textColor=TEXT,
        spaceAfter=6, spaceBefore=2
    )
    s['body_bold'] = ParagraphStyle(
        'body_bold', fontName='Helvetica-Bold',
        fontSize=10, leading=16, textColor=TEXT, spaceAfter=4
    )
    s['bullet'] = ParagraphStyle(
        'bullet', fontName='Helvetica',
        fontSize=10, leading=16, textColor=TEXT,
        leftIndent=14, spaceAfter=3,
        bulletIndent=4, bulletFontName='Helvetica',
        bulletFontSize=12
    )
    s['code'] = ParagraphStyle(
        'code', fontName='Courier',
        fontSize=9, leading=14, textColor=colors.HexColor("#2B6CB0"),
        backColor=colors.HexColor("#EBF8FF"),
        leftIndent=10, rightIndent=10, spaceAfter=4,
    )
    s['warning'] = ParagraphStyle(
        'warning', fontName='Helvetica',
        fontSize=10, leading=15, textColor=colors.HexColor("#742A2A"),
        leftIndent=10, rightIndent=10, spaceAfter=4
    )
    s['tip'] = ParagraphStyle(
        'tip', fontName='Helvetica',
        fontSize=10, leading=15, textColor=colors.HexColor("#22543D"),
        leftIndent=10, rightIndent=10, spaceAfter=4
    )
    s['footer'] = ParagraphStyle(
        'footer', fontName='Helvetica',
        fontSize=8, leading=12, textColor=MID_GRAY,
        alignment=TA_CENTER
    )
    s['page_num'] = ParagraphStyle(
        'page_num', fontName='Helvetica',
        fontSize=8, leading=12, textColor=MID_GRAY,
        alignment=TA_RIGHT
    )
    s['glossary_term'] = ParagraphStyle(
        'glossary_term', fontName='Helvetica-Bold',
        fontSize=10, leading=15, textColor=accent,
        spaceAfter=1, spaceBefore=5
    )
    s['glossary_def'] = ParagraphStyle(
        'glossary_def', fontName='Helvetica',
        fontSize=10, leading=15, textColor=TEXT,
        leftIndent=16, spaceAfter=2
    )
    return s


class ColorBox(Flowable):
    def __init__(self, width, height, color, radius=4):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height,
                            self.radius, fill=1, stroke=0)


class SectionHeader(Flowable):
    def __init__(self, number, title, accent=ACCENT, width=None):
        super().__init__()
        self.number = number
        self.title = title
        self.accent = accent
        self.width = width or (PAGE_W - 2 * MARGIN)
        self.height = 28

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        c.bookmarkPage(f'sec-{self.number}')
        c.setFillColor(ACCENT2)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=0)
        c.setFillColor(self.accent)
        c.roundRect(0, 0, 36, h, 4, fill=1, stroke=0)
        c.rect(28, 0, 8, h, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(18, h / 2 - 5, self.number)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(44, h / 2 - 5, self.title.upper())

    def wrap(self, availW, availH):
        return self.width, self.height


def make_cover(story, styles, role_label, subtitle, accent, update_date):
    story.append(Spacer(1, 30 * mm))

    logo_text = Paragraph(
        "<font color='#E94560'>◈</font>  "
        "<font color='white'>ValBelluna</font>"
        "<font color='#E94560'> Motorsport</font>",
        ParagraphStyle('logo', fontName='Helvetica-Bold', fontSize=28,
                       leading=36, textColor=WHITE, alignment=TA_CENTER)
    )

    role_p = Paragraph(role_label.upper(),
        ParagraphStyle('role_tag', fontName='Helvetica-Bold', fontSize=11,
                       textColor=WHITE, alignment=TA_CENTER)
    )
    role_box = Table([[role_p]], colWidths=[80 * mm], rowHeights=[10 * mm])
    role_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent),
        ('ROUNDEDCORNERS', [5]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    title_p = Paragraph("Guida Completa", styles['cover_title'])
    sub_p = Paragraph(subtitle, styles['cover_subtitle'])
    date_p = Paragraph(f"Aggiornato al: {update_date}",
        ParagraphStyle('cdate', fontName='Helvetica', fontSize=9,
                       textColor=colors.HexColor("#718096"), alignment=TA_CENTER)
    )

    role_centered = Table([[role_box]], colWidths=[PAGE_W - 2 * MARGIN])
    role_centered.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.extend([
        logo_text,
        Spacer(1, 8 * mm),
        role_centered,
        Spacer(1, 8 * mm),
        title_p,
        sub_p,
        Spacer(1, 6 * mm),
        HRFlowable(width=60 * mm, thickness=1.5, color=accent,
                   hAlign='CENTER', spaceAfter=6 * mm),
        date_p,
        PageBreak()
    ])


def make_toc(story, styles, items, accent):
    story.append(Spacer(1, 4 * mm))
    title = Paragraph("Indice", ParagraphStyle(
        'toc_h', fontName='Helvetica-Bold', fontSize=18,
        textColor=DARK, spaceAfter=4
    ))
    story.append(title)
    story.append(HRFlowable(width='100%', thickness=2, color=accent,
                            spaceAfter=8 * mm))

    accent_hex = f'#{accent.hexval()[2:]}'
    toc_rows = []
    for num, label in items:
        num_p = Paragraph(
            f'<a href="#sec-{num}" color="{accent_hex}">'
            f'<font color="{accent_hex}">{num}</font></a>',
            ParagraphStyle('tn', fontName='Helvetica-Bold', fontSize=11,
                           textColor=accent, alignment=TA_RIGHT)
        )
        lbl_p = Paragraph(
            f'<a href="#sec-{num}" color="{accent_hex}">'
            f'<font color="{accent_hex}"><u>{label}</u></font></a>',
            ParagraphStyle('tl', fontName='Helvetica', fontSize=11,
                           textColor=accent)
        )
        toc_rows.append([num_p, lbl_p])

    toc_t = Table(toc_rows, colWidths=[20 * mm, PAGE_W - 2 * MARGIN - 24 * mm])
    toc_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, BORDER),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 8),
        ('LEFTPADDING', (1, 0), (1, -1), 4),
    ]))
    story.append(toc_t)
    story.append(PageBreak())


def make_page_template(accent, role_label):
    def on_page(canvas, doc):
        canvas.saveState()
        w, h = A4

        canvas.setStrokeColor(accent)
        canvas.setLineWidth(2)
        canvas.line(MARGIN, h - 12 * mm, w - MARGIN, h - 12 * mm)

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(DARK)
        canvas.drawString(MARGIN, h - 9 * mm, APP_NAME)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawRightString(w - MARGIN, h - 9 * mm, role_label)

        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 14 * mm, w - MARGIN, 14 * mm)

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(MARGIN, 10 * mm, "Uso interno — Documento riservato")
        canvas.drawRightString(w - MARGIN, 10 * mm, f"Pag. {doc.page}")

        canvas.restoreState()
    return on_page


# ── TXT Parser ─────────────────────────────────────────────────────────────

def parse_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cover_info = {}
    elements = []
    i = 0

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        line = raw.rstrip('\n')

        # Cover directive
        if stripped.startswith('[COVER'):
            m = re.match(r'\[COVER subtitle="([^"]*)"\s*\|\s*role=([^|]+)\s*\|\s*date=([^\]]+)\]', stripped)
            if m:
                cover_info = {'subtitle': m.group(1), 'role': m.group(2).strip(), 'date': m.group(3).strip()}
            i += 1
            continue

        # Blank line
        if not stripped:
            i += 1
            continue

        # Section: "= 1. TITLE ="
        m = re.match(r'^=\s*(\d+)\.\s+(.+?)\s*=$', stripped)
        if m:
            elements.append(('section', (m.group(1), m.group(2).strip())))
            i += 1
            continue

        # Subsection: "== 1.1 TITLE =="
        m = re.match(r'^==\s*([\d.]+)\s+(.+?)\s*==$', stripped)
        if m:
            elements.append(('subsection', (m.group(1), m.group(2).strip())))
            i += 1
            continue

        # Warning
        if stripped.startswith('[WARNING]'):
            text = stripped[9:].strip()
            text = _collect_continuation(lines, i + 1, text)
            elements.append(('warning', text))
            # find how many lines were consumed
            consumed = 1
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (lines[j].startswith('  ') or lines[j].startswith('\t')):
                    consumed += 1
                else:
                    break
            i += consumed
            continue

        # Tip
        if stripped.startswith('[TIP]'):
            text = stripped[5:].strip()
            text = _collect_continuation(lines, i + 1, text)
            elements.append(('tip', text))
            consumed = 1
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (lines[j].startswith('  ') or lines[j].startswith('\t')):
                    consumed += 1
                else:
                    break
            i += consumed
            continue

        # Info
        if stripped.startswith('[INFO'):
            content = stripped[5:].strip().rstrip(']').strip()
            if '|' in content:
                label, value = content.split('|', 1)
                elements.append(('info', (label.strip(), value.strip())))
            i += 1
            continue

        # Code
        if stripped.startswith('[CODE]'):
            text = stripped[6:].strip()
            text = _collect_continuation(lines, i + 1, text)
            elements.append(('code', text))
            consumed = 1
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (lines[j].startswith('  ') or lines[j].startswith('\t')):
                    consumed += 1
                else:
                    break
            i += consumed
            continue

        # Glossary start
        if stripped == '[GLOSSARY]':
            entries = []
            i += 1
            while i < len(lines):
                gl = lines[i].strip()
                if gl == '[/GLOSSARY]':
                    i += 1
                    break
                if '—' in gl:
                    term, defn = gl.split('—', 1)
                    entries.append((term.strip(), defn.strip()))
                elif entries:
                    pt, pd = entries[-1]
                    entries[-1] = (pt, pd + ' ' + gl)
                i += 1
            elements.append(('glossary', entries))
            continue

        # Bullet
        if stripped.startswith('- '):
            text = stripped[2:].strip()
            text = _collect_continuation(lines, i + 1, text)
            elements.append(('bullet', text))
            consumed = 1
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (lines[j].startswith('    ') or lines[j].startswith('\t')):
                    consumed += 1
                else:
                    break
            i += consumed
            continue

        # Body text (indented)
        if line.startswith('  ') or line.startswith('\t'):
            text = stripped
            text = _collect_continuation(lines, i + 1, text)
            elements.append(('body', text))
            consumed = 1
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (lines[j].startswith('  ') or lines[j].startswith('\t')):
                    consumed += 1
                else:
                    break
            i += consumed
            continue

        i += 1

    return cover_info, elements


def _collect_continuation(lines, start, initial_text):
    text = initial_text
    for j in range(start, len(lines)):
        l = lines[j]
        if l.strip() and (l.startswith('  ') or l.startswith('\t')):
            text += ' ' + l.strip()
        else:
            break
    return text


# ── PDF Builder ────────────────────────────────────────────────────────────

def build_pdf(path, cover_info, elements, accent, role_label):
    styles = make_styles(accent)

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"{APP_NAME} – {role_label}",
        author=APP_NAME
    )

    story = []

    # Cover
    make_cover(story, styles, role_label, cover_info.get('subtitle', ''),
               accent, cover_info.get('date', ''))

    # Build TOC
    toc_items = []
    for el_type, el_data in elements:
        if el_type == 'section':
            num, title = el_data
            toc_items.append((num, title))
    make_toc(story, styles, toc_items, accent)

    # Build content
    for el_type, el_data in elements:
        if el_type == 'section':
            num, title = el_data
            story.append(Spacer(1, 4 * mm))
            story.append(SectionHeader(num, title, accent))
            story.append(Spacer(1, 3 * mm))

        elif el_type == 'subsection':
            sub_num, sub_title = el_data
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(sub_title, styles['subsection']))
            story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=3))

        elif el_type == 'body':
            story.append(Paragraph(el_data, styles['body']))

        elif el_type == 'bullet':
            story.append(Paragraph(f"•  {el_data}", styles['body']))

        elif el_type == 'warning':
            story.append(warning_box(el_data, styles, is_tip=False))

        elif el_type == 'tip':
            story.append(warning_box(el_data, styles, is_tip=True))

        elif el_type == 'code':
            story.append(Paragraph(f"<font face='Courier'>{el_data}</font>", styles['code']))

        elif el_type == 'info':
            label, value = el_data
            story.append(info_row(label, value, styles, accent))

        elif el_type == 'glossary':
            for term, defn in el_data:
                story.append(Paragraph(term, styles['glossary_term']))
                story.append(Paragraph(defn, styles['glossary_def']))
            story.append(Spacer(1, 4 * mm))

    doc.build(story,
              onFirstPage=make_page_template(accent, role_label),
              onLaterPages=make_page_template(accent, role_label))
    print(f"  ✓ {path}")


def warning_box(text, styles, is_tip=False):
    bg = TIP_BG if is_tip else WARN_BG
    border = TIP_BORDER if is_tip else WARN_BORDER
    icon = "✓" if is_tip else "⚠"
    style = styles['tip'] if is_tip else styles['warning']
    content = f"<b>{icon}  </b>{text}"
    t = Table([[Paragraph(content, style)]], colWidths=[PAGE_W - 2 * MARGIN - 4])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1.2, border),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def info_row(label, value, styles, accent=ACCENT):
    lbl = Paragraph(f"<b>{label}</b>", styles['body_bold'])
    val = Paragraph(
        f"<font color='#{accent.hexval()[2:]}' name='Helvetica-Bold'>{value}</font>",
        styles['body'])
    t = Table([[lbl, val]], colWidths=[60 * mm, PAGE_W - 2 * MARGIN - 64 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('LINEAFTER', (0, 0), (0, -1), 0.5, BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))

    configs = [
        ("istruzioni-utente.txt", "guida-utente.pdf", "Guida Utente"),
        ("istruzioni-admin.txt", "guida-admin.pdf", "Guida Amministratore"),
        ("istruzioni-superadmin.txt", "guida-superadmin.pdf", "Guida SuperAdmin"),
    ]

    print(f"Generazione PDF {APP_NAME}...")
    for txt_name, pdf_name, role_label in configs:
        txt_path = os.path.join(base, txt_name)
        pdf_path = os.path.join(base, pdf_name)
        accent = ACCENTS[role_label]
        cover_info, elements = parse_txt(txt_path)
        build_pdf(pdf_path, cover_info, elements, accent, role_label)
    print("Completato.")
