import ipaddress
import logging
from io import BytesIO
from typing import Any
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.base import BaseHTTPMiddleware

_log = logging.getLogger(__name__)

from app.config import settings
from app.database import get_db
import app.models  # noqa: F401 - register all ORM models
from app.auth import get_current_user, normalize_role
from app.models import (
    BundleInclude,
    Client,
    ClientProfile,
    Kit,
    KitDocumentTemplate,
    KitQuestion,
    KitQuestionOption,
    KitResult,
    KitRule,
    KitSection,
    KitSubmission,
    KitVersion,
    User,
)
from app.webhooks.clerk import router as clerk_router
from app.pdf import build_kit_pdf
from app.risk_engine import calculate_result_from_risks
from app.rules import calculate_result
from app.schemas import (
    AdminGrantSubscriptionPayload,
    AdminUpdateUserRolePayload,
    AdminUserResponse,
    AdminKitResponse,
    AdminKitUpdatePayload,
    AnswersPayload,
    ClientCreate,
    ClientResponse,
    KitDefinitionResponse,
    KitOption,
    KitQuestionResponse,
    KitSectionResponse,
    KitSummaryResponse,
    ResultResponse,
    RuleResponse,
)
from app.seed_data import PROFILE_GENERAL_DEFINITION, seed_database


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
# Schema migrations are run externally by Alembic (`alembic upgrade head`),
# typically from the container's start.sh on boot. Do NOT call
# Base.metadata.create_all here in production.
# ---------------------------------------------------------------------------
app = FastAPI(title=settings.app_name, version="0.1.0")

# Clerk webhook routes (no auth — verified via svix signature)
app.include_router(clerk_router)


# ---------------------------------------------------------------------------
# IP allowlist — private beta gate
# ---------------------------------------------------------------------------
# If ALLOWED_IPS env var is set, only those IPs / CIDRs can reach the API.
# Empty list = fail-open (no restriction). /health and /api/webhooks/* are
# always exempted so Railway healthchecks and provider webhooks (Stripe,
# Clerk, etc.) keep working.
# ---------------------------------------------------------------------------
_EXEMPT_PREFIXES = ("/health", "/api/webhooks/")


def _client_ip(request: Request) -> str | None:
    # Railway puts a proxy in front; the original client IP is the leftmost
    # entry of X-Forwarded-For. Fall back to the direct peer if missing.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else None


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path == p or path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        networks = settings.allowed_networks
        if not networks:
            # Gate disabled — let everything through.
            return await call_next(request)

        raw = _client_ip(request)
        if not raw:
            _log.warning("IP allowlist: no client IP found, denying")
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
        try:
            ip_obj = ipaddress.ip_address(raw)
        except ValueError:
            _log.warning("IP allowlist: bad client IP %r, denying", raw)
            return JSONResponse({"detail": "Forbidden"}, status_code=403)

        if not any(ip_obj in net for net in networks):
            _log.info("IP allowlist: denying %s on %s", raw, path)
            return JSONResponse({"detail": "Forbidden"}, status_code=403)

        return await call_next(request)


app.add_middleware(IPAllowlistMiddleware)


# ---------------------------------------------------------------------------
# CORS — strict list from env (no more wildcard)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def _is_admin(user: User) -> bool:
    return normalize_role(user.role) in {"admin", "super_admin"}


def _is_super_admin(user: User) -> bool:
    return normalize_role(user.role) == "super_admin"


def require_admin_user(user: User = Depends(get_current_user)) -> User:
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_super_admin_user(user: User = Depends(get_current_user)) -> User:
    if not _is_super_admin(user):
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user


# ---------------------------------------------------------------------------
# Startup — optional seeding (guarded by env flag)
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    if not settings.seed_on_startup:
        return
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_client(db: Session, client_id: int, user: User) -> Client:
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id,
            Client.user_id == user.id,
            Client.deleted_at.is_(None),
        )
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def _get_kit(db: Session, code: str) -> Kit:
    kit = db.query(Kit).filter(Kit.code == code).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Kit not found")
    return kit


def _has_full_kit_access(user: User) -> bool:
    return normalize_role(user.role) in {"admin", "super_admin"}


def _user_has_kit_access(db: Session, user_id: int, kit_id: int) -> bool:
    direct = (
        db.query(Subscription.id)
        .join(Product, Product.id == Subscription.product_id)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Product.active == True,
            Product.type == "kit",
            Product.kit_id == kit_id,
        )
        .first()
    )
    if direct:
        return True

    bundle = (
        db.query(Subscription.id)
        .join(Product, Product.id == Subscription.product_id)
        .join(BundleInclude, BundleInclude.bundle_product_id == Product.id)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Product.active == True,
            Product.type == "bundle",
            BundleInclude.kit_id == kit_id,
        )
        .first()
    )
    return bundle is not None


def _require_kit_access(db: Session, user: User, kit: Kit) -> None:
    if _has_full_kit_access(user):
        return
    if not _user_has_kit_access(db, user.id, kit.id):
        raise HTTPException(status_code=402, detail="Kit subscription required")


def _get_published_version(db: Session, kit_id: int) -> KitVersion:
    version = (
        db.query(KitVersion)
        .options(
            joinedload(KitVersion.sections).joinedload(KitSection.questions).joinedload(KitQuestion.options),
            joinedload(KitVersion.sections).joinedload(KitSection.questions).joinedload(KitQuestion.risk_maps),
            joinedload(KitVersion.rules),
            joinedload(KitVersion.templates),
        )
        .filter(KitVersion.kit_id == kit_id, KitVersion.status == "published")
        .order_by(KitVersion.version_number.desc())
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Published kit version not found")
    return version


def _serialize_definition(kit: Kit, version: KitVersion) -> dict[str, Any]:
    sections = []
    for section in sorted(version.sections, key=lambda item: item.display_order):
        questions = []
        for question in sorted(section.questions, key=lambda item: item.display_order):
            opts = [
                KitOption(value=opt.value, label=opt.label, score_hint=opt.score_hint)
                for opt in sorted(question.options, key=lambda item: item.display_order)
            ]
            if question.question_type == "risk_matrix" and not opts and question.responsabil_options_json:
                opts = [KitOption(value=x, label=x, score_hint=None) for x in question.responsabil_options_json]
            questions.append(
                KitQuestionResponse(
                    id=question.id,
                    question_key=question.question_key,
                    label=question.label,
                    help_text=question.help_text,
                    question_type=question.question_type,
                    required=question.required,
                    display_order=question.display_order,
                    options=opts,
                    responsabil_options=question.responsabil_options_json,
                )
            )
        sections.append(
            KitSectionResponse(
                id=section.id,
                title=section.title,
                description=section.description,
                display_order=section.display_order,
                questions=questions,
            )
        )
    return KitDefinitionResponse(
        id=kit.id,
        code=kit.code,
        name=kit.name,
        description=kit.description,
        documentation_url=kit.documentation_url,
        pricing_type=kit.pricing_type,
        price_eur=kit.price_eur,
        version_number=version.version_number,
        sections=sections,
    ).model_dump()


def _latest_submission(db: Session, client_id: int, kit_id: int) -> KitSubmission | None:
    return (
        db.query(KitSubmission)
        .filter(KitSubmission.client_id == client_id, KitSubmission.kit_id == kit_id)
        .order_by(KitSubmission.updated_at.desc())
        .first()
    )


def _latest_result(db: Session, client_id: int, kit_id: int) -> KitResult | None:
    return (
        db.query(KitResult)
        .filter(KitResult.client_id == client_id, KitResult.kit_id == kit_id)
        .order_by(KitResult.calculated_at.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": settings.app_name, "environment": settings.environment}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/profile/definition")
def get_profile_definition():
    return PROFILE_GENERAL_DEFINITION


@app.get("/api/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": normalize_role(user.role),
    }


@app.get("/api/products", response_model=list[ProductSummaryResponse])
def list_products(
    db: Session = Depends(get_db),
):
    return db.query(Product).filter(Product.active == True).order_by(Product.display_order.asc()).all()


@app.get("/api/clients", response_model=list[ClientResponse])
def list_clients(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Client)
        .filter(Client.user_id == user.id, Client.deleted_at.is_(None))
        .order_by(Client.created_at.desc())
        .all()
    )


@app.post("/api/clients", response_model=ClientResponse)
def create_client(
    payload: ClientCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = Client(
        user_id=user.id,
        name=payload.name,
        company_name=payload.company_name,
        notes=payload.notes,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    db.add(ClientProfile(client_id=client.id, answers_json={}, status="draft", version=1))
    db.commit()
    return client


@app.get("/api/clients/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_client(db, client_id, user)


@app.get("/api/clients/{client_id}/profile")
def get_client_profile(
    client_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client(db, client_id, user)
    profile = db.query(ClientProfile).filter(ClientProfile.client_id == client_id).first()
    return {
        "definition": PROFILE_GENERAL_DEFINITION,
        "answers": profile.answers_json if profile else {},
        "status": profile.status if profile else "draft",
    }


@app.put("/api/clients/{client_id}/profile")
def save_client_profile(
    client_id: int,
    payload: AnswersPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client(db, client_id, user)
    profile = db.query(ClientProfile).filter(ClientProfile.client_id == client_id).first()
    if not profile:
        profile = ClientProfile(client_id=client_id)
        db.add(profile)
    profile.answers_json = payload.answers
    profile.status = "completed"
    profile.version = (profile.version or 0) + 1
    db.commit()
    db.refresh(profile)
    return {"answers": profile.answers_json, "status": profile.status, "version": profile.version}


@app.get("/api/kits", response_model=list[KitSummaryResponse])
def list_kits(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    kits = db.query(Kit).filter(Kit.active == True).order_by(Kit.display_order.asc()).all()
    if _has_full_kit_access(user):
        return kits
    return [kit for kit in kits if _user_has_kit_access(db, user.id, kit.id)]


@app.get("/api/kits/{kit_code}")
def get_kit_definition(
    kit_code: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kit = _get_kit(db, kit_code)
    _require_kit_access(db, user, kit)
    version = _get_published_version(db, kit.id)
    return _serialize_definition(kit, version)


@app.get("/api/clients/{client_id}/kits/{kit_code}")
def get_kit_submission_view(
    client_id: int,
    kit_code: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client(db, client_id, user)
    kit = _get_kit(db, kit_code)
    _require_kit_access(db, user, kit)
    version = _get_published_version(db, kit.id)
    submission = _latest_submission(db, client_id, kit.id)
    result = _latest_result(db, client_id, kit.id)
    return {
        "definition": _serialize_definition(kit, version),
        "submission": submission.answers_json if submission else {},
        "result": ResultResponse(
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            risk_flags_json=result.risk_flags_json,
            responsibility_matrix_json=result.responsibility_matrix_json,
            engagement_level=result.engagement_level,
            tariff_adjustment_pct=getattr(result, "tariff_adjustment_pct", 0.0),
            active_risks_json=getattr(result, "active_risks_json", []),
            result_json=result.result_json,
        ).model_dump() if result else None,
    }


@app.put("/api/clients/{client_id}/kits/{kit_code}")
def save_kit_submission(
    client_id: int,
    kit_code: str,
    payload: AnswersPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client(db, client_id, user)
    kit = _get_kit(db, kit_code)
    _require_kit_access(db, user, kit)
    version = _get_published_version(db, kit.id)
    submission = _latest_submission(db, client_id, kit.id)
    if not submission:
        submission = KitSubmission(
            user_id=user.id,
            client_id=client_id,
            kit_id=kit.id,
            kit_version_id=version.id,
        )
        db.add(submission)
    submission.answers_json = payload.answers
    submission.status = "completed"
    submission.kit_version_id = version.id
    db.flush()

    has_risk_maps = any(
        q.risk_maps for s in version.sections for q in s.questions
    )
    if has_risk_maps:
        calc = calculate_result_from_risks(db, version.id, payload.answers)
    else:
        rules_payload = [
            {"rule_code": r.rule_code, "priority": r.priority, "active": r.active,
             "conditions_json": r.conditions_json, "effects_json": r.effects_json}
            for r in version.rules
        ]
        calc = calculate_result(payload.answers, rules_payload)
        calc.setdefault("tariff_adjustment_pct", 0.0)
        calc.setdefault("active_risks_json", [])

    result = _latest_result(db, client_id, kit.id)
    if not result:
        result = KitResult(
            user_id=user.id,
            client_id=client_id,
            kit_id=kit.id,
            kit_version_id=version.id,
            submission_id=submission.id,
        )
        db.add(result)
    result.kit_version_id = version.id
    result.submission_id = submission.id
    result.risk_score = calc["risk_score"]
    result.risk_level = calc["risk_level"]
    result.risk_flags_json = calc["risk_flags_json"]
    result.responsibility_matrix_json = calc["responsibility_matrix_json"]
    result.engagement_level = calc["engagement_level"]
    result.tariff_adjustment_pct = calc.get("tariff_adjustment_pct", 0.0)
    result.active_risks_json = calc.get("active_risks_json", [])
    result.result_json = calc["result_json"]

    db.commit()
    return {"submission": submission.answers_json, "result": calc}


@app.get("/api/clients/{client_id}/kits/{kit_code}/result", response_model=ResultResponse)
def get_kit_result(
    client_id: int,
    kit_code: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client(db, client_id, user)
    kit = _get_kit(db, kit_code)
    _require_kit_access(db, user, kit)
    result = _latest_result(db, client_id, kit.id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return ResultResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        risk_flags_json=result.risk_flags_json,
        responsibility_matrix_json=result.responsibility_matrix_json,
        engagement_level=result.engagement_level,
        tariff_adjustment_pct=getattr(result, "tariff_adjustment_pct", 0.0),
        active_risks_json=getattr(result, "active_risks_json", []),
        result_json=result.result_json,
    )


@app.get("/api/clients/{client_id}/kits/{kit_code}/pdf")
def get_kit_pdf(
    client_id: int,
    kit_code: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = _get_client(db, client_id, user)
    kit = _get_kit(db, kit_code)
    _require_kit_access(db, user, kit)
    version = _get_published_version(db, kit.id)
    submission = _latest_submission(db, client_id, kit.id)
    result = _latest_result(db, client_id, kit.id)
    if not submission or not result:
        raise HTTPException(status_code=400, detail="Submission or result missing")

    template = next((item for item in version.templates if item.document_type == "result_pdf"), None)
    question_labels = {}
    for section in version.sections:
        for question in section.questions:
            question_labels[question.question_key] = question.label
    pdf_bytes = build_kit_pdf(
        client_name=client.name,
        kit_name=kit.name,
        submission=submission.answers_json,
        result={
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "risk_flags_json": result.risk_flags_json,
            "responsibility_matrix_json": result.responsibility_matrix_json,
            "engagement_level": result.engagement_level,
            "tariff_adjustment_pct": getattr(result, "tariff_adjustment_pct", 0.0),
            "active_risks_json": getattr(result, "active_risks_json", []),
        },
        template={
            "title": template.title if template else f"{kit.name} - Raport",
            "intro_text": template.intro_text if template else "",
            "signature_block_text": template.signature_block_text if template else "Semnatura",
        },
        question_labels=question_labels,
    )
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf")


# ---------------------------------------------------------------------------
# Admin routes — role-based access (admin/super_admin)
# ---------------------------------------------------------------------------
@app.get("/api/admin/kits/{kit_code}", response_model=AdminKitResponse)
def get_admin_kit(
    kit_code: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin_user),
):
    kit = _get_kit(db, kit_code)
    version = _get_published_version(db, kit.id)
    definition = _serialize_definition(kit, version)
    template = next((item for item in version.templates if item.document_type == "result_pdf"), None)
    return AdminKitResponse(
        kit=KitDefinitionResponse(**definition),
        rules=[
            RuleResponse(
                id=rule.id,
                rule_code=rule.rule_code,
                name=rule.name,
                description=rule.description,
                priority=rule.priority,
                active=rule.active,
                conditions_json=rule.conditions_json,
                effects_json=rule.effects_json,
            )
            for rule in sorted(version.rules, key=lambda item: item.priority)
        ],
        template={
            "title": template.title if template else "",
            "intro_text": template.intro_text if template else "",
            "footer_text": template.footer_text if template else "",
            "signature_block_text": template.signature_block_text if template else "",
        },
    )


@app.put("/api/admin/kits/{kit_code}")
def update_admin_kit(
    kit_code: str,
    payload: AdminKitUpdatePayload,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin_user),
):
    kit = _get_kit(db, kit_code)
    version = _get_published_version(db, kit.id)

    if payload.name is not None:
        kit.name = payload.name
    if payload.description is not None:
        kit.description = payload.description
    if payload.price_eur is not None:
        kit.price_eur = payload.price_eur

    for section in list(version.sections):
        db.delete(section)
    for rule in list(version.rules):
        db.delete(rule)

    template = next((item for item in version.templates if item.document_type == "result_pdf"), None)
    if not template:
        template = KitDocumentTemplate(kit_version_id=version.id, document_type="result_pdf", title=kit.name)
        db.add(template)

    db.flush()

    for section_index, section_data in enumerate(payload.sections, start=1):
        section = KitSection(
            kit_version_id=version.id,
            title=section_data["title"],
            description=section_data.get("description"),
            display_order=section_index,
        )
        db.add(section)
        db.flush()

        for question_index, question_data in enumerate(section_data.get("questions", []), start=1):
            question = KitQuestion(
                kit_section_id=section.id,
                question_key=question_data["question_key"],
                label=question_data["label"],
                help_text=question_data.get("help_text"),
                question_type=question_data["question_type"],
                required=question_data.get("required", False),
                display_order=question_index,
            )
            db.add(question)
            db.flush()
            for option_index, option in enumerate(question_data.get("options", []), start=1):
                db.add(
                    KitQuestionOption(
                        question_id=question.id,
                        value=option["value"],
                        label=option["label"],
                        score_hint=option.get("score_hint"),
                        display_order=option_index,
                    )
                )

    for rule_data in payload.rules:
        db.add(
            KitRule(
                kit_version_id=version.id,
                rule_code=rule_data["rule_code"],
                name=rule_data["name"],
                description=rule_data.get("description"),
                priority=rule_data.get("priority", 100),
                active=rule_data.get("active", True),
                conditions_json=rule_data.get("conditions_json", {}),
                effects_json=rule_data.get("effects_json", {}),
            )
        )

    template.title = payload.template.get("title", kit.name)
    template.intro_text = payload.template.get("intro_text")
    template.footer_text = payload.template.get("footer_text")
    template.signature_block_text = payload.template.get("signature_block_text")

    db.commit()
    return {"ok": True}


@app.put("/api/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: AdminUpdateUserRolePayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_super_admin_user),
):
    requested_role = normalize_role(payload.role)
    if requested_role not in {"client", "admin", "super_admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    target = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    current_role = normalize_role(target.role)
    if current_role == requested_role:
        return {
            "ok": True,
            "user_id": target.id,
            "old_role": current_role,
            "new_role": requested_role,
        }

    if current_role == "super_admin" and requested_role != "super_admin":
        super_admin_count = (
            db.query(User)
            .filter(User.deleted_at.is_(None), User.role.in_(["super_admin"]))
            .count()
        )
        if super_admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last super_admin")

    target.role = requested_role
    db.commit()

    _log.info(
        "Role changed by user_id=%s: target_user_id=%s %s -> %s",
        actor.id,
        target.id,
        current_role,
        requested_role,
    )
    return {
        "ok": True,
        "user_id": target.id,
        "old_role": current_role,
        "new_role": requested_role,
    }


@app.get("/api/admin/users", response_model=list[AdminUserResponse])
def list_admin_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin_user),
):
    users = (
        db.query(User)
        .filter(User.deleted_at.is_(None))
        .order_by(User.created_at.asc())
        .all()
    )
    return [
        AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=normalize_role(user.role),
            created_at=user.created_at,
        )
        for user in users
    ]


@app.post("/api/admin/users/{user_id}/subscriptions")
def grant_user_subscription(
    user_id: int,
    payload: AdminGrantSubscriptionPayload,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin_user),
):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    product = db.query(Product).filter(Product.code == payload.product_code, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.product_id == product.id,
            Subscription.status == "active",
        )
        .first()
    )
    if existing:
        return {"ok": True, "subscription_id": existing.id, "already_active": True}

    now = datetime.utcnow()
    period_days = 30 if payload.billing_cycle == "monthly" else 365
    sub = Subscription(
        user_id=user.id,
        product_id=product.id,
        status="active",
        billing_cycle=payload.billing_cycle,
        current_period_start=now,
        current_period_end=now + timedelta(days=period_days),
        cancel_at_period_end=False,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"ok": True, "subscription_id": sub.id, "already_active": False}
    Product,
    Subscription,
    ProductSummaryResponse,
