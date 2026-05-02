"""Seed pentru platforma Kit - riscuri, kituri, chestionare."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.kit_questions_data import KIT_ADMINISTRATIV, KIT_RISC_EXTINS_QUESTIONS, RESPONSABIL_OPTS
from app.models import (
    BundleInclude,
    Kit,
    KitDocumentTemplate,
    KitQuestion,
    KitQuestionOption,
    KitRule,
    KitSection,
    KitVersion,
    Product,
    QuestionRiskMap,
    Risk,
)
from app.risks_data import RISKS_50

PROFILE_GENERAL_DEFINITION = [
    {
        "id": "identificare",
        "title": "Identificare entitate",
        "questions": [
            {"key": "denumire_entitate", "label": "Denumire entitate", "type": "text", "required": True},
            {"key": "cui", "label": "Cod unic de inregistrare", "type": "text", "required": True},
            {"key": "forma_juridica", "label": "Forma juridica", "type": "single_choice", "required": True, "options": ["SRL", "PFA", "II", "IF", "Alta"]},
            {"key": "caen_principal", "label": "Cod CAEN principal", "type": "text", "required": False},
            {"key": "administrator", "label": "Administrator / reprezentant legal", "type": "text", "required": True},
            {"key": "beneficiar_real", "label": "Beneficiar real", "type": "text", "required": False},
        ],
    },
    {
        "id": "context_operational",
        "title": "Context operational",
        "questions": [
            {"key": "domeniu_activitate", "label": "Domeniu principal de activitate", "type": "text", "required": False},
            {"key": "nr_documente_luna", "label": "Numar estimat documente / luna", "type": "number", "required": False},
            {"key": "nr_conturi_bancare", "label": "Numar conturi bancare", "type": "number", "required": False},
            {"key": "nr_angajati", "label": "Numar angajati", "type": "number", "required": False},
            {"key": "persoana_contact", "label": "Persoana responsabila transmitere documente", "type": "text", "required": False},
            {"key": "canale_comunicare", "label": "Canale de comunicare", "type": "multi_choice", "required": False, "options": ["email", "telefon", "whatsapp", "Platforme online"]},
        ],
    },
]

KIT_DEFS = [
    {"code": "internal_fiscal_procedures", "name": "Risc general administrativ", "description": "Responsabilitate, trasabilitate și fluxuri interne pentru relația cu contabilul.", "documentation_url": "/docs/kit-internal_fiscal_procedures.pdf", "price_eur": 45.0},
    {"code": "digital_recurring_compliance", "name": "Risc fiscal", "description": "TVA, deductibilitate, tratament fiscal. Implementare flux digital.", "documentation_url": "/docs/kit-digital_recurring_compliance.pdf", "price_eur": 45.0},
    {"code": "tax_residency_nonresidents", "name": "Risc rezidenta fiscala", "description": "Impozit reținut la sursă, convenții fiscale, tranzacții internaționale.", "documentation_url": "/docs/kit-tax_residency_nonresidents.pdf", "price_eur": 55.0},
    {"code": "affiliate_compliance", "name": "Risc Afiliati", "description": "Transfer pricing, tranzacții intra-grup cu părți afiliate.", "documentation_url": "/docs/kit-affiliate_compliance.pdf", "price_eur": 45.0},
    {"code": "affiliate_identification", "name": "Risc extins (ESG)", "description": "Chestionar complet – toate cele 50 de riscuri. Environmental, Social, Governance.", "documentation_url": "/docs/kit-affiliate_identification.pdf", "price_eur": 55.0},
]


def _get_risk_by_code(db: Session, code: str) -> Risk | None:
    return db.query(Risk).filter(Risk.code == code).first()


def _seed_risks(db: Session) -> dict[str, Risk]:
    if db.query(Risk).count() > 0:
        return {r.code: r for r in db.query(Risk).all()}
    risk_map = {}
    for i, r in enumerate(RISKS_50):
        risk = Risk(
            code=r["code"],
            category=r["category"],
            name=r["name"],
            impact_default=r.get("impact", 2),
            probability_default=r.get("probability", 2),
            display_order=i + 1,
        )
        db.add(risk)
        db.flush()
        risk_map[risk.code] = risk
    return risk_map


def _build_questions_from_admin(version_id: int, risk_map: dict[str, Risk]) -> list[tuple[KitQuestion, list[tuple[bool, str]]]]:
    result = []
    section_order = 0
    for sec in KIT_ADMINISTRATIV["sections"]:
        section_order += 1
        for q_idx, q in enumerate(sec["questions"]):
            question = KitQuestion(
                kit_section_id=version_id,  # will be set after section
                question_key=q["key"],
                label=q["label"],
                question_type="risk_matrix",
                required=True,
                display_order=q_idx + 1,
                responsabil_options_json=RESPONSABIL_OPTS,
            )
            mappings = []
            for code in q.get("trigger_nu", []):
                mappings.append((False, code))
            for code in q.get("trigger_da", []):
                mappings.append((True, code))
            result.append((question, mappings))
    return result


def _build_questions_from_risc_extins(version_id: int, risk_map: dict[str, Risk]) -> list[tuple[KitQuestion, list[tuple[bool, str]]]]:
    result = []
    for sec in KIT_RISC_EXTINS_QUESTIONS:
        for q_idx, q in enumerate(sec["questions"]):
            question = KitQuestion(
                kit_section_id=version_id,
                question_key=q["key"],
                label=q["label"],
                question_type="risk_matrix",
                required=True,
                display_order=q_idx + 1,
                responsabil_options_json=RESPONSABIL_OPTS,
            )
            mappings = []
            for code in q.get("trigger_nu", []):
                mappings.append((False, code))
            for code in q.get("trigger_da", []):
                mappings.append((True, code))
            result.append((question, mappings))
    return result


def seed_database(db: Session) -> None:
    risk_map = _seed_risks(db)

    if db.query(Kit).count() == 0:
        for idx, kdef in enumerate(KIT_DEFS):
            kit = Kit(
                code=kdef["code"],
                name=kdef["name"],
                description=kdef["description"],
                documentation_url=kdef.get("documentation_url"),
                display_order=idx + 1,
                pricing_type="one_time",
                price_eur=kdef["price_eur"],
                active=True,
            )
            db.add(kit)
            db.flush()

            version = KitVersion(
                kit_id=kit.id,
                version_number=1,
                status="published",
                notes="Seed V2 – 32 întrebări, 50 riscuri",
                published_at=datetime.utcnow(),
            )
            db.add(version)
            db.flush()

            if kdef["code"] == "internal_fiscal_procedures":
                _seed_kit_from_admin(db, version, kit, risk_map)
            elif kdef["code"] == "affiliate_identification":
                _seed_kit_from_risc_extins(db, version, kit, risk_map)
            else:
                _seed_kit_generic(db, version, kit, risk_map, kdef["code"])

            db.add(
                KitDocumentTemplate(
                    kit_version_id=version.id,
                    document_type="result_pdf",
                    title=f"{kit.name} - Raport",
                    intro_text=f"Raport metodologic pentru {kit.name}.",
                    footer_text="Document generat din Kit Platform V2.",
                    signature_block_text="Semnatura administrator / reprezentant legal",
                    show_risk_score=True,
                    show_risk_flags=True,
                    show_responsibility_matrix=True,
                    show_tariff_recommendation=True,
                    template_json={},
                )
            )

    _seed_products_catalog(db)

    db.commit()


def _seed_products_catalog(db: Session) -> None:
    kits = db.query(Kit).order_by(Kit.display_order.asc()).all()
    if not kits:
        return

    for order, kit in enumerate(kits, start=1):
        code = f"kit_{kit.code}"
        product = db.query(Product).filter(Product.code == code).first()
        if product:
            product.name = kit.name
            product.type = "kit"
            product.kit_id = kit.id
            product.active = True
            product.display_order = order
        else:
            db.add(
                Product(
                    code=code,
                    name=kit.name,
                    type="kit",
                    kit_id=kit.id,
                    display_order=order,
                    active=True,
                )
            )

    bundle = db.query(Product).filter(Product.code == "bundle_all_kits").first()
    if not bundle:
        bundle = Product(
            code="bundle_all_kits",
            name="Bundle toate kiturile",
            type="bundle",
            kit_id=None,
            display_order=len(kits) + 1,
            active=True,
        )
        db.add(bundle)
        db.flush()
    else:
        bundle.name = "Bundle toate kiturile"
        bundle.type = "bundle"
        bundle.kit_id = None
        bundle.active = True

    existing = {(row.bundle_product_id, row.kit_id) for row in db.query(BundleInclude).filter(BundleInclude.bundle_product_id == bundle.id).all()}
    for kit in kits:
        key = (bundle.id, kit.id)
        if key not in existing:
            db.add(BundleInclude(bundle_product_id=bundle.id, kit_id=kit.id))


def _seed_kit_from_admin(db: Session, version: KitVersion, kit: Kit, risk_map: dict[str, Risk]) -> None:
    for sec_idx, sec in enumerate(KIT_ADMINISTRATIV["sections"]):
        section = KitSection(
            kit_version_id=version.id,
            title=sec["title"],
            description=sec.get("description"),
            display_order=sec_idx + 1,
        )
        db.add(section)
        db.flush()

        for q_idx, q in enumerate(sec["questions"]):
            question = KitQuestion(
                kit_section_id=section.id,
                question_key=q["key"],
                label=q["label"],
                question_type="risk_matrix",
                required=True,
                display_order=q_idx + 1,
                responsabil_options_json=RESPONSABIL_OPTS,
            )
            db.add(question)
            db.flush()

            for code in q.get("trigger_nu", []):
                r = risk_map.get(code)
                if r:
                    db.add(QuestionRiskMap(question_id=question.id, risk_id=r.id, trigger_on_true=False))
            for code in q.get("trigger_da", []):
                r = risk_map.get(code)
                if r:
                    db.add(QuestionRiskMap(question_id=question.id, risk_id=r.id, trigger_on_true=True))


def _seed_kit_from_risc_extins(db: Session, version: KitVersion, kit: Kit, risk_map: dict[str, Risk]) -> None:
    for sec_idx, sec in enumerate(KIT_RISC_EXTINS_QUESTIONS):
        section = KitSection(
            kit_version_id=version.id,
            title=sec["title"],
            description=sec.get("description", ""),
            display_order=sec_idx + 1,
        )
        db.add(section)
        db.flush()

        for q_idx, q in enumerate(sec["questions"]):
            question = KitQuestion(
                kit_section_id=section.id,
                question_key=q["key"],
                label=q["label"],
                question_type="risk_matrix",
                required=True,
                display_order=q_idx + 1,
                responsabil_options_json=RESPONSABIL_OPTS,
            )
            db.add(question)
            db.flush()

            for code in q.get("trigger_nu", []):
                r = risk_map.get(code)
                if r:
                    db.add(QuestionRiskMap(question_id=question.id, risk_id=r.id, trigger_on_true=False))
            for code in q.get("trigger_da", []):
                r = risk_map.get(code)
                if r:
                    db.add(QuestionRiskMap(question_id=question.id, risk_id=r.id, trigger_on_true=True))


def _seed_kit_generic(db: Session, version: KitVersion, kit: Kit, risk_map: dict[str, Risk], code: str) -> None:
    """Kituri Fiscal, Nerezidenți, Afiliați – folosesc structura Risc Extins pentru MVP."""
    _seed_kit_from_risc_extins(db, version, kit, risk_map)
    Product,
