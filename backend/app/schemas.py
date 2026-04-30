from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ClientCreate(BaseModel):
    name: str
    company_name: str | None = None
    notes: str | None = None


class ClientResponse(BaseModel):
    id: int
    name: str
    company_name: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AnswersPayload(BaseModel):
    answers: dict[str, Any]


class KitOption(BaseModel):
    value: str
    label: str
    score_hint: float | None = None


class KitQuestionResponse(BaseModel):
    id: int
    question_key: str
    label: str
    help_text: str | None
    question_type: str
    required: bool
    display_order: int
    options: list[KitOption]
    responsabil_options: list[str] | None = None


class KitSectionResponse(BaseModel):
    id: int
    title: str
    description: str | None
    display_order: int
    questions: list[KitQuestionResponse]


class KitSummaryResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    documentation_url: str | None = None
    pricing_type: str
    price_eur: float
    active: bool
    display_order: int

    class Config:
        from_attributes = True


class KitDefinitionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    documentation_url: str | None = None
    pricing_type: str
    price_eur: float
    version_number: int
    sections: list[KitSectionResponse]


class RuleResponse(BaseModel):
    id: int
    rule_code: str
    name: str
    description: str | None
    priority: int
    active: bool
    conditions_json: dict[str, Any]
    effects_json: dict[str, Any]


class AdminKitResponse(BaseModel):
    kit: KitDefinitionResponse
    rules: list[RuleResponse]
    template: dict[str, Any]


class AdminKitUpdatePayload(BaseModel):
    name: str | None = None
    description: str | None = None
    price_eur: float | None = None
    sections: list[dict[str, Any]]
    rules: list[dict[str, Any]]
    template: dict[str, Any]


class ResultResponse(BaseModel):
    risk_score: float
    risk_level: str
    risk_flags_json: list[str]
    responsibility_matrix_json: list[dict[str, Any]]
    engagement_level: str
    tariff_adjustment_pct: float = 0.0
    active_risks_json: list[dict[str, Any]] = []
    result_json: dict[str, Any]


class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUpdateUserRolePayload(BaseModel):
    role: str
