"""Motor Risk Matrix – mapare întrebări → riscuri, scor = Prob × Impact × Coef responsabilitate."""

from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models import KitQuestion, KitSection, KitVersion, QuestionRiskMap
from app.risks_data import RESPONSABIL_COEF, RISK_LEVEL_THRESHOLDS, TARIFF_ADJUSTMENT


def _get_answer_value(answers: dict, key: str) -> tuple[bool | None, str | None]:
    """Returnează (answer: bool?, responsabil: str?) pentru o întrebare."""
    val = answers.get(key)
    if val is None:
        return None, None
    if isinstance(val, dict):
        ans = val.get("answer")
        resp = val.get("responsabil", "delegat")
        if ans is None and "value" in val:
            ans = val["value"]
        return (bool(ans) if ans is not None else None), (resp or "delegat")
    return bool(val), "delegat"


def _score_to_level(score: float) -> str:
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if score <= threshold:
            return level
    return "CRITICAL"


def calculate_result_from_risks(
    db: Session,
    kit_version_id: int,
    answers: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculează rezultatul pe baza mapării întrebări → riscuri.
    answers: { "q1_1": { "answer": true, "responsabil": "administrator" }, ... }
    """
    version = (
        db.query(KitVersion)
        .options(
            joinedload(KitVersion.sections)
            .joinedload(KitSection.questions)
            .joinedload(KitQuestion.risk_maps)
            .joinedload(QuestionRiskMap.risk),
        )
        .filter(KitVersion.id == kit_version_id)
        .first()
    )
    if not version:
        return _empty_result()

    risk_scores: dict[int, float] = {}
    risk_responsibles: dict[int, str] = {}
    responsibility_entries: list[dict] = []

    for section in sorted(version.sections, key=lambda s: s.display_order):
        for question in sorted(section.questions, key=lambda q: q.display_order):
            answer_val, responsabil = _get_answer_value(answers, question.question_key)
            if answer_val is None:
                continue

            coef = RESPONSABIL_COEF.get(responsabil.lower() if responsabil else "delegat", 1.0)

            for qrm in question.risk_maps:
                if qrm.trigger_on_true != answer_val:
                    continue
                risk = qrm.risk
                prob = qrm.probability_override or risk.probability_default
                impact = qrm.impact_override or risk.impact_default
                score = prob * impact * coef

                risk_scores[risk.id] = risk_scores.get(risk.id, 0) + score
                risk_responsibles[risk.id] = responsabil or "delegat"
                responsibility_entries.append({
                    "area": risk.name,
                    "responsible_party": responsabil or "Entitate",
                    "risk_code": risk.code,
                })

    total_score = sum(risk_scores.values())
    risk_level = _score_to_level(total_score)
    tariff_pct = TARIFF_ADJUSTMENT.get(risk_level, 0)

    active_risks = []
    for rid, r in [(m.risk_id, m.risk) for s in version.sections for q in s.questions for m in q.risk_maps]:
        if rid in risk_scores and r.code not in [ar["code"] for ar in active_risks]:
            active_risks.append({
                "code": r.code,
                "name": r.name,
                "score": risk_scores[rid],
                "responsible": risk_responsibles.get(rid, "delegat"),
            })

    dedup_matrix: list[dict] = []
    seen = set()
    for entry in responsibility_entries:
        key = (entry["area"], entry["responsible_party"])
        if key in seen:
            continue
        seen.add(key)
        dedup_matrix.append({"area": entry["area"], "responsible_party": entry["responsible_party"]})

    risk_flags = [ar["code"] for ar in active_risks]

    engagement = "standard"
    if risk_level in ("HIGH", "CRITICAL"):
        engagement = "ridicat"
    elif risk_level == "MEDIUM":
        engagement = "mediu"

    return {
        "risk_score": round(total_score, 1),
        "risk_level": risk_level,
        "risk_flags_json": risk_flags,
        "responsibility_matrix_json": dedup_matrix,
        "engagement_level": engagement,
        "tariff_adjustment_pct": tariff_pct,
        "active_risks_json": active_risks,
        "result_json": {"total_score": total_score, "risk_level": risk_level},
    }


def _empty_result() -> dict:
    return {
        "risk_score": 0.0,
        "risk_level": "LOW",
        "risk_flags_json": [],
        "responsibility_matrix_json": [],
        "engagement_level": "standard",
        "tariff_adjustment_pct": 0.0,
        "active_risks_json": [],
        "result_json": {},
    }
