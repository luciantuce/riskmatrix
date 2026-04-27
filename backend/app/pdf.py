from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def _humanize_key(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _humanize_flag(value: str) -> str:
    return _humanize_key(value)


def build_kit_pdf(
    client_name: str,
    kit_name: str,
    submission: dict,
    result: dict,
    template: dict,
    question_labels: dict[str, str] | None = None,
) -> bytes:
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

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, template.get("title") or f"{kit_name} - Raport")
    y -= 24

    c.setFont("Helvetica", 11)
    c.drawString(x, y, f"Client: {client_name}")
    y -= 18
    intro = template.get("intro_text") or ""
    c.drawString(x, y, intro)
    y -= 26

    c.setStrokeColor(colors.HexColor("#dbe4f0"))
    c.line(x, y, width - x, y)
    y -= 24

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Raspunsuri")
    y -= 18
    c.setFont("Helvetica", 10)
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
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, f"{label}:")
        y -= 14
        c.setFont("Helvetica", 10)
        c.drawString(x + 10, y, display_value)
        y -= 18
        y = new_page_if_needed(y)

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Rezultat")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"Scor risc: {result.get('risk_score', 0)}")
    y -= 14
    c.drawString(x, y, f"Nivel risc: {result.get('risk_level', 'LOW')}")
    y -= 14
    c.drawString(x, y, f"Nivel implicare: {result.get('engagement_level', 'standard')}")
    y -= 14
    c.drawString(x, y, f"Ajustare onorariu: +{result.get('tariff_adjustment_pct', 0)}%")
    y -= 14

    active_risks = result.get("active_risks_json") or []
    flags = result.get("risk_flags_json") or []
    if active_risks:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "Riscuri identificate:")
        y -= 14
        c.setFont("Helvetica", 10)
        for ar in active_risks:
            name = ar.get("name") or ar.get("code", "")
            c.drawString(x + 10, y, f"- {name}")
            y -= 14
            y = new_page_if_needed(y)
    elif flags:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "Flag-uri identificate:")
        y -= 14
        c.setFont("Helvetica", 10)
        for flag in flags:
            c.drawString(x + 10, y, f"- {_humanize_flag(flag)}")
            y -= 14
            y = new_page_if_needed(y)

    matrix = result.get("responsibility_matrix_json") or []
    if matrix:
        y -= 6
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Matrice responsabilitati")
        y -= 16
        c.setFont("Helvetica", 10)
        for row in matrix:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, y, row.get("area") or "Domeniu")
            y -= 14
            c.setFont("Helvetica", 10)
            c.drawString(x + 10, y, f"Responsabil: {row.get('responsible_party')}")
            y -= 18
            y = new_page_if_needed(y)

    y -= 18
    c.setStrokeColor(colors.HexColor("#dbe4f0"))
    c.line(x, y, width - x, y)
    y -= 28
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, template.get("signature_block_text") or "Semnatura administrator / reprezentant legal")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(x, y, "Nume: __________________________________________")
    y -= 18
    c.drawString(x, y, "Data: ____________________   Semnatura: ____________________")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
