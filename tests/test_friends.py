"""
test_friends.py — SnapIT
Tests del sistema de amigos e historial.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool

import api.database as db_module
test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

# ── Setup: crear dos usuarios y obtener sus tokens ────────────────────────

def setup_users():
    r1 = client.post("/register", json={
        "username": "alice", "display_name": "Alice",
        "email": "alice@test.com", "password": "pass123"
    })
    r2 = client.post("/register", json={
        "username": "bob", "display_name": "Bob",
        "email": "bob@test.com", "password": "pass123"
    })
    r3 = client.post("/register", json={
        "username": "carol", "display_name": "Carol",
        "email": "carol@test.com", "password": "pass123"
    })
    return r1.json()["access_token"], r2.json()["access_token"], r3.json()["access_token"]

token_alice, token_bob, token_carol = setup_users()
auth_alice = {"Authorization": f"Bearer {token_alice}"}
auth_bob   = {"Authorization": f"Bearer {token_bob}"}
auth_carol = {"Authorization": f"Bearer {token_carol}"}


# ── Tests de amigos ───────────────────────────────────────────────────────

def test_send_friend_request():
    r = client.post("/friends/bob", headers=auth_alice)
    assert r.status_code == 200
    assert "enviada" in r.json()["message"]
    print(f"  ✅ Alice envía solicitud a Bob  →  {r.json()['message']}")


def test_send_duplicate_request():
    r = client.post("/friends/bob", headers=auth_alice)
    assert r.status_code == 409
    print("  ✅ Solicitud duplicada  →  409")


def test_self_request():
    r = client.post("/friends/alice", headers=auth_alice)
    assert r.status_code == 400
    print("  ✅ Auto-solicitud  →  400")


def test_request_nonexistent_user():
    r = client.post("/friends/nobody_xyz", headers=auth_alice)
    assert r.status_code == 404
    print("  ✅ Usuario inexistente  →  404")


def test_bob_sees_pending_request():
    r = client.get("/friends", headers=auth_bob)
    assert r.status_code == 200
    data = r.json()
    assert len(data["pending_received"]) == 1
    assert data["pending_received"][0]["username"] == "alice"
    print(f"  ✅ Bob ve solicitud pendiente de Alice")


def test_alice_sees_sent_request():
    r = client.get("/friends", headers=auth_alice)
    data = r.json()
    assert len(data["pending_sent"]) == 1
    assert data["pending_sent"][0]["username"] == "bob"
    assert len(data["friends"]) == 0
    print(f"  ✅ Alice ve solicitud enviada a Bob")


def test_accept_friend_request():
    r = client.post("/friends/alice/accept", headers=auth_bob)
    assert r.status_code == 200
    assert "amigo" in r.json()["message"]
    print(f"  ✅ Bob acepta a Alice  →  {r.json()['message']}")


def test_both_see_each_other_as_friends():
    ra = client.get("/friends", headers=auth_alice)
    rb = client.get("/friends", headers=auth_bob)
    da = ra.json(); db_ = rb.json()
    assert len(da["friends"]) == 1 and da["friends"][0]["username"] == "bob"
    assert len(db_["friends"]) == 1 and db_["friends"][0]["username"] == "alice"
    assert len(da["pending_sent"])     == 0
    assert len(da["pending_received"]) == 0
    print("  ✅ Alice y Bob se ven mutuamente como amigos")


def test_already_friends_error():
    r = client.post("/friends/bob", headers=auth_alice)
    assert r.status_code == 409
    assert "amigos" in r.json()["detail"]
    print("  ✅ Ya son amigos  →  409")


def test_search_users():
    r = client.get("/friends/search?q=aro", headers=auth_alice)
    assert r.status_code == 200
    results = r.json()
    assert any(u["username"] == "carol" for u in results)
    print(f"  ✅ Búsqueda 'aro'  →  {[u['username'] for u in results]}")


def test_search_shows_friend_status():
    r = client.get("/friends/search?q=bob", headers=auth_alice)
    results = r.json()
    bob_result = next(u for u in results if u["username"] == "bob")
    assert bob_result["status"] == "accepted"
    print(f"  ✅ Búsqueda muestra status correcto: bob → {bob_result['status']}")


def test_search_too_short():
    r = client.get("/friends/search?q=ab", headers=auth_alice)
    assert r.status_code == 400
    print("  ✅ Búsqueda < 3 chars  →  400")


def test_remove_friend():
    # Carol envía a Alice, Alice acepta, luego la elimina
    client.post("/friends/alice", headers=auth_carol)
    client.post("/friends/carol/accept", headers=auth_alice)
    r = client.delete("/friends/carol", headers=auth_alice)
    assert r.status_code == 200
    # Verificar que ya no son amigos
    ra = client.get("/friends", headers=auth_alice)
    assert not any(f["username"] == "carol" for f in ra.json()["friends"])
    print("  ✅ Eliminar amigo  →  OK")


def test_friends_only_feed():
    # Sin amigos que hayan jugado, el feed de amigos está vacío
    r = client.get("/feed?friends_only=true", headers=auth_alice)
    assert r.status_code == 200
    print(f"  ✅ Feed amigos (vacío)  →  {len(r.json()['entries'])} entradas")


def test_feed_without_auth():
    r = client.get("/feed")
    assert r.status_code == 200
    print(f"  ✅ Feed global sin auth  →  OK ({len(r.json()['entries'])} entradas)")


# ── Tests de historial ────────────────────────────────────────────────────

def test_history_empty():
    r = client.get("/user/alice/history", headers=auth_alice)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "alice"
    assert data["entries"] == []
    assert data["calendar"] == []
    print("  ✅ Historial vacío  →  OK")


def test_history_nonexistent_user():
    r = client.get("/user/nobody_xyz/history", headers=auth_alice)
    assert r.status_code == 404
    print("  ✅ Historial usuario inexistente  →  404")


def test_history_no_images_for_non_friend():
    # Carol no es amiga de Alice → no debe ver imágenes del historial de Alice
    r = client.get("/user/alice/history", headers=auth_carol)
    assert r.status_code == 200
    for entry in r.json()["entries"]:
        assert entry["annotated_image_b64"] is None
    print("  ✅ No-amigo no ve imágenes en historial")


# ── Runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    groups = [
        ("👥 AMIGOS", [
            test_send_friend_request, test_send_duplicate_request,
            test_self_request, test_request_nonexistent_user,
            test_bob_sees_pending_request, test_alice_sees_sent_request,
            test_accept_friend_request, test_both_see_each_other_as_friends,
            test_already_friends_error, test_search_users,
            test_search_shows_friend_status, test_search_too_short,
            test_remove_friend,
        ]),
        ("🌐 FEED",      [test_friends_only_feed, test_feed_without_auth]),
        ("📅 HISTORIAL", [test_history_empty, test_history_nonexistent_user,
                          test_history_no_images_for_non_friend]),
    ]
    total = passed = 0
    for group, fns in groups:
        print(f"\n{group}")
        for fn in fns:
            total += 1
            try:
                fn(); passed += 1
            except Exception as e:
                print(f"  ❌ {fn.__name__}: {e}")
    print(f"\n{'─'*44}")
    print(f"  {passed}/{total} tests passed {'✅' if passed == total else '⚠️'}")
