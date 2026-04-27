#!/usr/bin/env python3
"""Generează PDF-uri placeholder pentru documentația fiecărui kit."""

import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Mapare kit code -> (titlu principal, subtitlu opțional)
KIT_DOCS = {
    "internal_fiscal_procedures": (
        "Risc general administrativ",
        "Responsabilitate, trasabilitate și fluxuri interne pentru relația cu contabilul.",
    ),
    "digital_recurring_compliance": (
        "Risc fiscal",
        "Implementare recurentă a responsabilităților și livrabilelor în flux digital.",
    ),
    "tax_residency_nonresidents": (
        "Risc rezidenta fiscala",
        "Evaluarea situațiilor de rezidență fiscală, obligații externe și activități transfrontaliere.",
    ),
    "affiliate_compliance": (
        "Risc Afiliati",
        "Analiza practică a tranzacțiilor intra-grup și a nivelului de conformare documentară.",
    ),
    "affiliate_identification": (
        "Risc extins (ESG)",
        "Cartografierea afiliaților, tranzacțiilor și analiza structurală a riscurilor (Environmental, Social, Governance).",
    ),
}

SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_DIR = Path(
    os.environ.get(
        "DOCS_OUTPUT_DIR",
        str(SCRIPT_DIR.parent.parent / "frontend" / "public" / "docs"),
    )
)


def build_placeholder_pdf(title: str, subtitle: str, output_path: Path) -> None:
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    x, y = 50, height - 80

    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, title)
    y -= 30

    c.setFont("Helvetica", 12)
    for line in subtitle.split(". "):
        if line.strip():
            c.drawString(x, y, line.strip() + ".")
            y -= 20

    y -= 30
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(x, y, "Guvernanța riscului profesional în activitatea contabilă")
    y -= 14
    c.drawString(x, y, "Dr. Lioara Veronica Pasc – Ediția I, 2026")
    y -= 30

    c.setFont("Helvetica-Oblique", 10)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawString(x, y, "Documentație – placeholder. Înlocuiți cu PDF-ul final.")
    c.save()


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for code, (title, subtitle) in KIT_DOCS.items():
        out = DOCS_DIR / f"kit-{code}.pdf"
        build_placeholder_pdf(title, subtitle, out)
        print(f"Scris: {out}")
    print("Gata.")


if __name__ == "__main__":
    main()
