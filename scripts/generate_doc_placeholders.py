#!/usr/bin/env python3
"""Generează PDF-uri placeholder pentru documentația fiecărui kit."""

import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Mapare kit code -> (titlu principal, subtitlu opțional)
KIT_DOCS = {
    "affiliate_compliance": (
        "Volumul I – Riscul profesional al contabilului",
        "Kit de conformare pentru tranzacții cu părți afiliate (prețuri de transfer)",
    ),
    "affiliate_identification": (
        "Volumul II – Risc extins",
        "Analiza structurală a riscurilor generate de activitatea economică. Kit de identificare a afilierii și tranzacțiilor cu părți afiliate.",
    ),
    "internal_fiscal_procedures": (
        "Volumul III – Metodologia MASS",
        "Model de analiză structurală a riscului profesional. Kit de proceduri fiscale interne (responsabilitate și trasabilitate).",
    ),
    "tax_residency_nonresidents": (
        "Volumul IV – Standardul de guvernanță a riscului profesional",
        "Kit de rezidență fiscală și nerezidenți.",
    ),
    "digital_recurring_compliance": (
        "Kit digital de conformare fiscală recurentă",
        "Implementare recurentă a responsabilităților și livrabilelor în flux digital (implementabil în TaxDome).",
    ),
}

SCRIPT_DIR = Path(__file__).resolve().parent
DOCS_DIR = Path(os.environ.get("DOCS_OUTPUT_DIR", str(SCRIPT_DIR.parent / "frontend" / "public" / "docs")))


def build_placeholder_pdf(title: str, subtitle: str, output_path: Path) -> None:
    width, height = A4
    c = canvas.Canvas(str(output_path), pagesize=A4)
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
