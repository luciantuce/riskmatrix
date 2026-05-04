"""
Clerk JWT authentication for FastAPI.

Flow:
  1. Frontend attaches `Authorization: Bearer <clerk_jwt>` on every request.
  2. `get_current_user` dependency decodes + verifies the JWT using Clerk's
     JWKS endpoint (RS256, cached by PyJWKClient).
  3. The `sub` claim is the Clerk user ID → looked up in the local `users` table.
  4. If the user row doesn't exist yet (webhook lag), it is lazy-created from
     JWT claims and a warning is logged.
"""

from functools import lru_cache

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.logging import log
from app.models import User

VALID_ROLES = {"client", "admin", "super_admin"}


def normalize_role(role: str | None) -> str:
    if role == "user":
        return "client"
    if role in VALID_ROLES:
        return role
    return "client"


def should_bootstrap_super_admin(email: str | None) -> bool:
    target = (settings.bootstrap_super_admin_email or "").strip().lower()
    current = (email or "").strip().lower()
    return bool(target and current and current == target)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    """Singleton JWKS client — caches signing keys automatically."""
    return PyJWKClient(settings.clerk_jwks_url, cache_keys=True)


def _decode_clerk_jwt(token: str) -> dict:
    """Verify Clerk JWT signature and return claims. Raises 401 on failure."""
    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured (CLERK_JWKS_URL missing)",
        )
    try:
        client = _jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — verifies Clerk JWT, returns the authenticated User.

    Usage:
        @app.get("/api/clients")
        def list_clients(user: User = Depends(get_current_user), ...):
            ...
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be: Bearer <token>",
        )

    token = authorization[len("Bearer "):].strip()
    claims = _decode_clerk_jwt(token)

    clerk_user_id: str = claims.get("sub", "")
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    user = (
        db.query(User)
        .filter(User.clerk_user_id == clerk_user_id, User.deleted_at.is_(None))
        .first()
    )

    if user:
        normalized = normalize_role(user.role)
        if should_bootstrap_super_admin(user.email):
            normalized = "super_admin"
        if normalized != user.role:
            user.role = normalized
            db.commit()
            db.refresh(user)
        return user

    # Webhook hasn't been processed yet — lazy-create from JWT claims.
    email = (
        claims.get("email")
        or _email_from_primary(claims)
        or f"{clerk_user_id}@clerk.placeholder"
    )
    first = claims.get("given_name") or claims.get("first_name") or ""
    last = claims.get("family_name") or claims.get("last_name") or ""
    full_name = f"{first} {last}".strip() or None

    log.warning("clerk_webhook_user_lazy_created", clerk_user_id=clerk_user_id)

    role = "super_admin" if should_bootstrap_super_admin(email) else "client"
    user = User(
        clerk_user_id=clerk_user_id,
        email=email,
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _email_from_primary(claims: dict) -> str | None:
    """Some Clerk JWT templates embed email_addresses list."""
    for addr in claims.get("email_addresses", []):
        if isinstance(addr, dict) and addr.get("email_address"):
            return addr["email_address"]
    return None
