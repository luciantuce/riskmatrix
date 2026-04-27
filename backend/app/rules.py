from typing import Any


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if op == "equals":
        return actual == expected
    if op == "not_equals":
        return actual != expected
    if op == "exists":
        return actual not in (None, "", [], {})
    if op == "contains":
        return isinstance(actual, list) and expected in actual
    if op == "greater_than":
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False
    return False


def evaluate_condition(condition: dict, answers: dict) -> bool:
    if "conditions" in condition:
        operator = condition.get("operator", "AND").upper()
        results = [evaluate_condition(item, answers) for item in condition.get("conditions", [])]
        return all(results) if operator == "AND" else any(results)

    field = condition.get("field")
    op = condition.get("op", "equals")
    expected = condition.get("value")
    actual = answers.get(field)
    return _compare(actual, op, expected)


def score_to_level(score: float) -> str:
    if score <= 2:
        return "LOW"
    if score <= 5:
        return "MEDIUM"
    if score <= 8:
        return "HIGH"
    return "CRITICAL"


def calculate_result(answers: dict, rules: list[dict]) -> dict:
    score = 0.0
    risk_flags: list[str] = []
    responsibility_matrix: list[dict] = []
    engagement_level = "standard"
    matched_rules: list[str] = []

    for rule in sorted(rules, key=lambda item: item.get("priority", 100)):
        if not rule.get("active", True):
            continue
        if not evaluate_condition(rule.get("conditions_json", {}), answers):
            continue

        matched_rules.append(rule["rule_code"])
        effects = rule.get("effects_json", {})
        score += float(effects.get("score_delta", 0))
        risk_flags.extend(effects.get("risk_flags", []))
        responsibility_matrix.extend(effects.get("responsibility_entries", []))
        if effects.get("engagement_level"):
            engagement_level = effects["engagement_level"]

    # dedupe while keeping order
    dedup_flags = list(dict.fromkeys(risk_flags))
    seen_matrix: set[tuple[tuple[str, Any], ...]] = set()
    dedup_matrix: list[dict] = []
    for entry in responsibility_matrix:
        marker = tuple(sorted(entry.items()))
        if marker in seen_matrix:
            continue
        seen_matrix.add(marker)
        dedup_matrix.append(entry)
    return {
        "risk_score": score,
        "risk_level": score_to_level(score),
        "risk_flags_json": dedup_flags,
        "responsibility_matrix_json": dedup_matrix,
        "engagement_level": engagement_level,
        "result_json": {"matched_rules": matched_rules},
    }
