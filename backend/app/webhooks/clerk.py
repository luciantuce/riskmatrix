"""
Clerk webhook handler.

Endpoint: POST /api/webhooks/clerk
Auth:     svix signature verified manually via HMAC-SHA256 (no svix lib needed)
Idempotency: webhook_events(source, external_id) UNIQUE constraint

Events handled:
  user.created  → INSERT users (upsert if lazy-create already ran)
  user.updated  → UPDATE email, full_name
  user.deleted  → soft-delete (deleted_at = now())
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.logging import log
from app.models import User, WebhookEvent

router = APIRouter()


def _verify_svix(
    payload: bytes,
    svix_id: str,
    svix_timestamp: str,
    svix_signature: str,
) -> dict:
    """
    Verify Clerk webhook signature without the svix library.
    Implements: https://docs.svix.com/receiving/verifying-payloads/how-manual
    """
    if not settings.clerk_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    # 1. Reject stale timestamps (>5 minutes)
    try:
        ts = int(svix_timestamp)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid svix-timestamp")
    if abs(int(time.time()) - ts) > 300:
        raise HTTPException(status_code=400, detail="Webhook timestamp too old or in future")

    # 2. Build signed content: "{svix_id}.{svix_timestamp}.{body}"
    signed = svix_id.encode() + b"." + svix_timestamp.encode() + b"." + payload

    # 3. Decode secret — format: "whsec_<base64>"
    secret = settings.clerk_webhook_secret
    if secret.startswith("whsec_"):
        secret = secret[6:]
    try:
        key = base64.b64decode(secret)
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid webhook secret format")

    # 4. Compute HMAC-SHA256 and compare
    expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()

    # Header can contain multiple space-separated signatures: "v1,<sig> v1,<sig2>"
    for sig in svix_signature.split(" "):
        if sig.startswith("v1,") and hmac.compare_digest(sig[3:], expected):
            return json.loads(payload)

    raise HTTPException(status_code=400, detail="Invalid webhook signature")


@router.post("/api/webhooks/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(..., alias="svix-id"),
    svix_timestamp: str = Header(..., alias="svix-timestamp"),
    svix_signature: str = Header(..., alias="svix-signature"),
    db: Session = Depends(get_db),
):
    body = await request.body()
    event = _verify_svix(body, svix_id, svix_timestamp, svix_signature)

    event_type: str = event.get("type", "")
    external_id: str = svix_id  # svix-id is the unique, stable event identifier

    # --- Idempotency check --------------------------------------------------
    existing = (
        db.query(WebhookEvent)
        .filter(
            WebhookEvent.source == "clerk",
            WebhookEvent.external_id == external_id,
        )
        .first()
    )
    if existing:
        log.info("clerk_webhook_duplicate", event_type=event_type, external_id=external_id)
        return {"ok": True}

    # --- Record event (before processing, so retries don't re-process) ------
    record = WebhookEvent(
        source="clerk",
        external_id=external_id,
        event_type=event_type,
        payload=event,
    )
    db.add(record)

    try:
        data = event.get("data", {})
        if event_type == "user.created":
            _on_user_created(db, data)
        elif event_type == "user.updated":
            _on_user_updated(db, data)
        elif event_type == "user.deleted":
            _on_user_deleted(db, data)
        else:
            log.info("clerk_webhook_unhandled_event_type", event_type=event_type)

        record.processed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        record.error = str(exc)
        db.commit()
        log.error(
            "clerk_webhook_handler_failed",
            event_type=event_type,
            external_id=external_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook handler error",
        )

    return {"ok": True}


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _on_user_created(db: Session, data: dict) -> None:
    clerk_user_id = data["id"]
    email = _primary_email(data)
    full_name = _full_name(data)

    # Upsert — lazy-create in auth.py may have already inserted this user
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if user:
        user.email = email
        user.full_name = full_name
        if user.role == "user":
            user.role = "client"
        user.updated_at = datetime.utcnow()
        log.info("clerk_user_created_updated_existing", clerk_user_id=clerk_user_id)
    else:
        db.add(User(clerk_user_id=clerk_user_id, email=email, full_name=full_name, role="client"))
        log.info("clerk_user_created_inserted", clerk_user_id=clerk_user_id, email=email)


def _on_user_updated(db: Session, data: dict) -> None:
    clerk_user_id = data["id"]
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not user:
        log.warning("clerk_user_updated_missing_local_user", clerk_user_id=clerk_user_id)
        db.add(User(
            clerk_user_id=clerk_user_id,
            email=_primary_email(data),
            full_name=_full_name(data),
            role="client",
        ))
    else:
        user.email = _primary_email(data)
        user.full_name = _full_name(data)
        if user.role == "user":
            user.role = "client"
        user.updated_at = datetime.utcnow()
        log.info("clerk_user_updated", clerk_user_id=clerk_user_id)


def _on_user_deleted(db: Session, data: dict) -> None:
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        return
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if user:
        user.deleted_at = datetime.utcnow()
        log.info("clerk_user_soft_deleted", clerk_user_id=clerk_user_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _primary_email(data: dict) -> str:
    emails = data.get("email_addresses", [])
    primary_id = data.get("primary_email_address_id")
    for e in emails:
        if e.get("id") == primary_id:
            return e["email_address"]
    if emails:
        return emails[0]["email_address"]
    return f"{data['id']}@unknown.clerk"


def _full_name(data: dict) -> str | None:
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    name = f"{first} {last}".strip()
    return name or None
