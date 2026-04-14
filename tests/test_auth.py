"""
test_auth.py — SnapIT
Tests del sistema de autenticación: registro, login, JWT, /me, /guest.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool

import api.database as db_module

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
db_module.engine = test_engine

from api.main import app
from api.database import get_session

def override_get_session():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session
SQLModel.metadata.create_all(test_engine)

client = TestClient(app)

# ── Datos de prueba ────────────────────────────────────────────────────────

VALID_USER = {
    "username":     "testauth",
    "display_name": "Test Auth",
    "email":        "testauth@example.com",
    "password":     "secret123",
}


# ── Registro ───────────────────────────────────────────────────────────────

def test_register_ok():
    r = client.post("/register", json=VALID_USER)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["username"] == VALID_USER["username"]
    assert data["is_guest"] == False
    print(f"  ✅ POST /register  →  token={data['access_token'][:20]}…")


def test_register_duplicate_username():
    r = client.post("/register", json={**VALID_USER, "email": "other@example.com"})
    assert r.status_code == 409
    assert "nombre de usuario" in r.json()["detail"]
    print("  ✅ Registro duplicado (username)  →  409")


def test_register_duplicate_email():
    r = client.post("/register", json={**VALID_USER, "username": "otherusr"})
    assert r.status_code == 409
    assert "email" in r.json()["detail"]
    print("  ✅ Registro duplicado (email)  →  409")


def test_register_short_password():
    r = client.post("/register", json={**VALID_USER, "username": "newuser2", "email": "new2@x.com", "password": "123"})
    assert r.status_code == 422   # Pydantic validation
    print("  ✅ Password corta  →  422")


# ── Login ──────────────────────────────────────────────────────────────────

def test_login_ok():
    r = client.post("/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["username"] == VALID_USER["username"]
    print(f"  ✅ POST /login  →  OK")
    return data["access_token"]


def test_login_wrong_password():
    r = client.post("/login", json={"email": VALID_USER["email"], "password": "wrongpassword"})
    assert r.status_code == 401
    print("  ✅ Login contraseña incorrecta  →  401")


def test_login_wrong_email():
    r = client.post("/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert r.status_code == 401
    print("  ✅ Login email inexistente  →  401")


# ── /me ────────────────────────────────────────────────────────────────────

def test_me_with_token():
    token = test_login_ok()
    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == VALID_USER["username"]
    assert data["email"]    == VALID_USER["email"]
    assert data["is_guest"] == False
    print(f"  ✅ GET /me  →  {data['username']} ({data['email']})")


def test_me_without_token():
    r = client.get("/me")
    assert r.status_code == 401
    print("  ✅ GET /me sin token  →  401")


def test_me_invalid_token():
    r = client.get("/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401
    print("  ✅ GET /me token inválido  →  401")


# ── Guest ──────────────────────────────────────────────────────────────────

def test_guest_create():
    r = client.post("/guest?username=guestuser&display_name=Guest+User")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "guestuser"
    assert data["is_guest"] == True
    assert "access_token" in data
    print(f"  ✅ POST /guest  →  {data['username']} (guest)")


def test_guest_idempotent():
    r1 = client.post("/guest?username=guestuser2&display_name=G2")
    r2 = client.post("/guest?username=guestuser2&display_name=G2")
    assert r1.status_code == 200
    assert r2.status_code == 200
    print("  ✅ Guest idempotente  →  mismo usuario, dos llamadas")


# ── Token en /today ────────────────────────────────────────────────────────

def test_today_with_token():
    token = test_login_ok()
    r = client.get("/today", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "object_name" in data
    assert data["already_done"] == False  # usuario recién registrado
    print(f"  ✅ GET /today con token  →  {data['object_emoji']} {data['object_name']}")


def test_today_without_token():
    r = client.get("/today")
    assert r.status_code == 200   # Funciona también sin token
    print("  ✅ GET /today sin token  →  OK (guest compatible)")


# ── Runner ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("🔐 REGISTRO", [test_register_ok, test_register_duplicate_username,
                          test_register_duplicate_email, test_register_short_password]),
        ("🔑 LOGIN",    [test_login_ok, test_login_wrong_password, test_login_wrong_email]),
        ("👤 /me",      [test_me_with_token, test_me_without_token, test_me_invalid_token]),
        ("👻 GUEST",    [test_guest_create, test_guest_idempotent]),
        ("🎯 AUTH+API", [test_today_with_token, test_today_without_token]),
    ]

    total = passed = 0
    for group, fns in tests:
        print(f"\n{group}")
        for fn in fns:
            total += 1
            try:
                fn()
                passed += 1
            except Exception as e:
                print(f"  ❌ {fn.__name__}: {e}")

    print(f"\n{'─'*42}")
    print(f"  {passed}/{total} tests passed {'✅' if passed == total else '⚠️'}")
