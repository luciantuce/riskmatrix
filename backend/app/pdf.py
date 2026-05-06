from io import BytesIO
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_REGULAR = "RiskMatrix-Regular"
FONT_BOLD = "RiskMatrix-Bold"
FONTS_REGISTERED = False


def _humanize_key(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _humanize_flag(value: str) -> str:
    return _humanize_key(value)


def _pdf_safe_text(value: object) -> str:
    return str(value or "")


def _register_fonts() -> tuple[str, str]:
    global FONTS_REGISTERED
    if FONTS_REGISTERED:
        return FONT_REGULAR, FONT_BOLD

    candidates = [
        (
            Path(__file__).resolve().parent / "assets" / "fonts" / "NotoSans-Regular.ttf",
            Path(__file__).resolve().parent / "assets" / "fonts" / "NotoSans-Bold.ttf",
        ),
        (
            Path(reportlab.__file__).resolve().parent / "fonts" / "Vera.ttf",
            Path(reportlab.__file__).resolve().parent / "fonts" / "VeraBd.ttf",
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
        ),
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular)))
            pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold)))
            FONTS_REGISTERED = True
            return FONT_REGULAR, FONT_BOLD
    return "Helvetica", "Helvetica-Bold"


def build_kit_pdf(
    client_name: str,
    kit_name: str,
    submission: dict,
    result: dict,
    template: dict,
    question_labels: dict[str, str] | None = None,
) -> bytes:
    font_regular, font_bold = _register_fonts()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 50
    y = height - 50
    question_labels = question_labels or {}

    def new_page_if_needed(current_y: int, threshold: int = 80) -> int:
        if current_y < threshold:
            c.showPage()
            return height - 50
        return current_y

    def draw_wrapped(
        text: str,
        current_x: int,
        current_y: int,
        font_name: str,
        font_size: int,
        line_height: int = 14,
    ) -> int:
        c.setFont(font_name, font_size)
        lines = simpleSplit(_pdf_safe_text(text), font_name, font_size, width - current_x * 2)
        for line in lines:
            c.drawString(current_x, current_y, line)
            current_y -= line_height
            current_y = new_page_if_needed(current_y)
        return current_y

    c.setFont(font_bold, 16)
    c.drawString(x, y, _pdf_safe_text(template.get("title") or f"{kit_name} - Raport"))
    y -= 24

    c.setFont(font_regular, 11)
    c.drawString(x, y, _pdf_safe_text(f"Client: {client_name}"))
    y -= 18
    intro = template.get("intro_text") or ""
    y = draw_wrapped(intro, x, y, font_regular, 11, 16)
    y -= 10

    c.setStrokeColor(colors.HexColor("#dbe4f0"))
    c.line(x, y, width - x, y)
    y -= 24

    c.setFont(font_bold, 12)
    c.drawString(x, y, _pdf_safe_text("Raspunsuri"))
    y -= 18
    c.setFont(font_regular, 10)
    for key, value in submission.items():
        if value is None:
            continue
        label = question_labels.get(key) or _humanize_key(key)
        if isinstance(value, dict) and "answer" in value:
            ans = "Da" if value.get("answer") else "Nu"
            resp = value.get("responsabil", "")
            display_value = f"{ans}" + (f" — {resp.capitalize()}" if resp else "")
        elif isinstance(value, list):
            display_value = ", ".join(str(v) for v in value)
        else:
            display_value = str(value)
        y = draw_wrapped(f"{label}:", x, y, font_bold, 10, 14)
        y = draw_wrapped(display_value, x + 10, y, font_regular, 10, 14)
        y -= 4
        y = new_page_if_needed(y)

    y -= 10
    c.setFont(font_bold, 12)
    c.drawString(x, y, _pdf_safe_text("Rezultat"))
    y -= 18
    c.setFont(font_regular, 10)
    c.drawString(x, y, _pdf_safe_text(f"Scor risc: {result.get('risk_score', 0)}"))
    y -= 14
    c.drawString(x, y, _pdf_safe_text(f"Nivel risc: {result.get('risk_level', 'LOW')}"))
    y -= 14
    c.drawString(
        x, y, _pdf_safe_text(f"Nivel implicare: {result.get('engagement_level', 'standard')}")
    )
    y -= 14
    c.drawString(
        x, y, _pdf_safe_text(f"Ajustare onorariu: +{result.get('tariff_adjustment_pct', 0)}%")
    )
    y -= 14

    active_risks = result.get("active_risks_json") or []
    flags = result.get("risk_flags_json") or []
    if active_risks:
        c.setFont(font_bold, 10)
        c.drawString(x, y, _pdf_safe_text("Riscuri identificate:"))
        y -= 14
        c.setFont(font_regular, 10)
        for ar in active_risks:
            name = ar.get("name") or ar.get("code", "")
            y = draw_wrapped(f"- {name}", x + 10, y, font_regular, 10, 14)
            y = new_page_if_needed(y)
    elif flags:
        c.setFont(font_bold, 10)
        c.drawString(x, y, _pdf_safe_text("Flag-uri identificate:"))
        y -= 14
        c.setFont(font_regular, 10)
        for flag in flags:
            y = draw_wrapped(f"- {_humanize_flag(flag)}", x + 10, y, font_regular, 10, 14)
            y = new_page_if_needed(y)

    matrix = result.get("responsibility_matrix_json") or []
    if matrix:
        y -= 6
        c.setFont(font_bold, 11)
        c.drawString(x, y, _pdf_safe_text("Matrice responsabilitati"))
        y -= 16
        c.setFont(font_regular, 10)
        for row in matrix:
            y = draw_wrapped(row.get("area") or "Domeniu", x, y, font_bold, 10, 14)
            y = draw_wrapped(
                f"Responsabil: {row.get('responsible_party')}", x + 10, y, font_regular, 10, 14
            )
            y -= 4
            y = new_page_if_needed(y)

    y -= 18
    c.setStrokeColor(colors.HexColor("#dbe4f0"))
    c.line(x, y, width - x, y)
    y -= 28
    c.setFont(font_bold, 11)
    c.drawString(
        x,
        y,
        _pdf_safe_text(
            template.get("signature_block_text") or "Semnatura administrator / reprezentant legal"
        ),
    )
    y -= 18
    c.setFont(font_regular, 10)
    c.drawString(x, y, _pdf_safe_text("Nume: __________________________________________"))
    y -= 18
    c.drawString(
        x, y, _pdf_safe_text("Data: ____________________   Semnatura: ____________________")
    )
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
