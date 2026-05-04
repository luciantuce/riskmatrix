from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

import app.auth as auth
from app.models import BundleInclude, Kit, Product, Subscription, User
from main import _user_has_kit_access


def test_normalize_role_maps_user_to_client():
    assert auth.normalize_role("user") == "client"


def test_normalize_role_keeps_valid_role():
    assert auth.normalize_role("admin") == "admin"


def test_normalize_role_falls_back_for_unknown_role():
    assert auth.normalize_role("manager") == "client"


def test_should_bootstrap_super_admin_true(monkeypatch):
    monkeypatch.setattr(auth.settings, "bootstrap_super_admin_email", "owner@example.com")
    assert auth.should_bootstrap_super_admin("owner@example.com") is True


def test_should_bootstrap_super_admin_false(monkeypatch):
    monkeypatch.setattr(auth.settings, "bootstrap_super_admin_email", "owner@example.com")
    assert auth.should_bootstrap_super_admin("other@example.com") is False


def test_get_current_user_rejects_non_bearer_header(db):
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(authorization="Token abc", db=db)
    assert exc.value.status_code == 401


def test_get_current_user_rejects_missing_sub_claim(monkeypatch, db):
    monkeypatch.setattr(auth, "_decode_clerk_jwt", lambda _token: {"email": "x@example.com"})
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(authorization="Bearer token", db=db)
    assert exc.value.status_code == 401


def test_get_current_user_returns_existing_user(monkeypatch, db):
    user = User(clerk_user_id="clerk_1", email="existing@example.com", role="client")
    db.add(user)
    db.commit()

    monkeypatch.setattr(
        auth,
        "_decode_clerk_jwt",
        lambda _token: {"sub": "clerk_1", "email": "existing@example.com"},
    )

    found = auth.get_current_user(authorization="Bearer token", db=db)
    assert found.id == user.id
    assert found.email == "existing@example.com"


def test_get_current_user_lazy_creates_user(monkeypatch, db):
    monkeypatch.setattr(
        auth,
        "_decode_clerk_jwt",
        lambda _token: {
            "sub": "clerk_new",
            "email": "new@example.com",
            "given_name": "New",
            "family_name": "User",
        },
    )

    created = auth.get_current_user(authorization="Bearer token", db=db)
    assert created.clerk_user_id == "clerk_new"
    assert created.email == "new@example.com"
    assert created.full_name == "New User"
    assert created.role == "client"


def test_user_has_kit_access_direct_subscription(db):
    user = User(clerk_user_id="u1", email="u1@example.com", role="client")
    kit = Kit(code="fiscal", name="Fiscal")
    product = Product(code="kit_fiscal", name="Kit Fiscal", type="kit", kit=kit, active=True)
    db.add_all([user, kit, product])
    db.commit()

    sub = Subscription(
        user_id=user.id,
        product_id=product.id,
        status="active",
        billing_cycle="monthly",
        current_period_start=datetime.utcnow() - timedelta(days=1),
        current_period_end=datetime.utcnow() + timedelta(days=29),
    )
    db.add(sub)
    db.commit()

    assert _user_has_kit_access(db, user.id, kit.id) is True


def test_user_has_kit_access_via_bundle(db):
    user = User(clerk_user_id="u2", email="u2@example.com", role="client")
    kit = Kit(code="tva", name="TVA")
    bundle = Product(code="bundle_all", name="Bundle", type="bundle", active=True)
    db.add_all([user, kit, bundle])
    db.commit()

    include = BundleInclude(bundle_product_id=bundle.id, kit_id=kit.id)
    db.add(include)
    db.commit()

    sub = Subscription(
        user_id=user.id,
        product_id=bundle.id,
        status="active",
        billing_cycle="monthly",
    )
    db.add(sub)
    db.commit()

    assert _user_has_kit_access(db, user.id, kit.id) is True


def test_user_has_kit_access_false_without_subscription(db):
    user = User(clerk_user_id="u3", email="u3@example.com", role="client")
    kit = Kit(code="rezidenta", name="Rezidenta")
    db.add_all([user, kit])
    db.commit()

    assert _user_has_kit_access(db, user.id, kit.id) is False


def test_user_has_kit_access_false_for_inactive_status(db):
    user = User(clerk_user_id="u4", email="u4@example.com", role="client")
    kit = Kit(code="afiliati", name="Afiliati")
    product = Product(code="kit_afiliati", name="Kit Afiliati", type="kit", kit=kit, active=True)
    db.add_all([user, kit, product])
    db.commit()

    sub = Subscription(user_id=user.id, product_id=product.id, status="canceled", billing_cycle="monthly")
    db.add(sub)
    db.commit()

    assert _user_has_kit_access(db, user.id, kit.id) is False
