"""
test_api.py — SnapIT
Tests de la API usando FastAPI TestClient.
No requiere levantar el servidor ni tener YOLOv8 instalado.
Se mockea el detector para los tests de /submit.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Usar base de datos en memoria para los tests
os.environ["SNAPIT_TEST"] = "1"

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool

# Parchear el engine ANTES de importar la app
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


# ─── Fixtures de detección mock ───────────────────────────────────────────────

def make_mock_detector(detected_class: str, confidence: float, bbox_ratio: float, others: int = 0):
    """Crea un detector falso que devuelve resultados controlados."""
    from core.detector import DetectionResult, Detection

    target_det = Detection(
        class_name=detected_class,
        confidence=confidence,
        bbox=(10, 10, 200, 200),
        bbox_area_ratio=bbox_ratio,
    ) if detected_class != "nothing" else None

    other_dets = [
        Detection(class_name=f"object_{i}", confidence=0.5,
                  bbox=(0,0,50,50), bbox_area_ratio=0.05)
        for i in range(others)
    ]
    all_dets = ([target_det] if target_det else []) + other_dets

    mock_result = DetectionResult(
        image_width=640,
        image_height=480,
        all_detections=all_dets,
        target_detection=target_det,
        annotated_image=b"fake_jpeg_bytes",
    )

    mock_detector = MagicMock()
    mock_detector.analyze.return_value = mock_result
    return mock_detector


def fake_image_bytes() -> bytes:
    """Bytes mínimos de una imagen JPEG válida."""
    # 1×1 pixel JPEG blanco
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04'
        b'\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa'
        b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd8\xff\xd9'
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "SnapIT"
    print("  ✅ GET /  →  OK")


def test_get_today():
    r = client.get("/today")
    assert r.status_code == 200
    data = r.json()
    assert "object_name" in data
    assert "difficulty" in data
    assert "base_points" in data
    assert data["already_done"] == False
    print(f"  ✅ GET /today  →  {data['object_emoji']} {data['object_name']} ({data['difficulty']})")


def test_get_today_with_username():
    r = client.get("/today?username=testuser")
    assert r.status_code == 200
    assert r.json()["already_done"] == False
    print("  ✅ GET /today?username=testuser  →  already_done=False")


def test_get_week():
    r = client.get("/week")
    assert r.status_code == 200
    week = r.json()["week"]
    assert len(week) == 7
    today_entries = [d for d in week if d["is_today"]]
    assert len(today_entries) == 1
    print(f"  ✅ GET /week  →  7 días, hoy={today_entries[0]['object_emoji']}")


def test_submit_correct_detection():
    from core.challenge import get_daily_challenge
    challenge = get_daily_challenge()

    mock_det = make_mock_detector(
        detected_class=challenge.coco_name,
        confidence=0.88,
        bbox_ratio=0.42,
        others=1,
    )

    with patch("api.main.get_detector", return_value=mock_det):
        r = client.post("/submit", data={
            "username": "testuser",
            "display_name": "Test User",
            "seconds_since_notification": 90,
            "attempt_number": 1,
        }, files={"photo": ("test.jpg", fake_image_bytes(), "image/jpeg")})

    assert r.status_code == 200
    data = r.json()
    assert data["correct"] == True
    assert data["total_score"] > 0
    assert data["speed_bonus"] == 500   # < 2 min = lightning
    assert data["framing_bonus"] == 300  # > 40% = perfect
    assert data["attempt_penalty"] == 0
    print(f"  ✅ POST /submit (correcto)  →  {data['total_score']} pts  conf={data['confidence_pct']}%")


def test_submit_wrong_detection():
    mock_det = make_mock_detector(
        detected_class="car",
        confidence=0.95,
        bbox_ratio=0.60,
        others=0,
    )

    with patch("api.main.get_detector", return_value=mock_det):
        r = client.post("/submit", data={
            "username": "testuser2",
            "display_name": "User 2",
            "seconds_since_notification": 60,
            "attempt_number": 1,
        }, files={"photo": ("test.jpg", fake_image_bytes(), "image/jpeg")})

    assert r.status_code == 200
    data = r.json()
    assert data["correct"] == False
    assert data["total_score"] == 0
    print(f"  ✅ POST /submit (incorrecto)  →  0 pts (detectado: {data['detected_class']})")


def test_submit_second_attempt():
    from core.challenge import get_daily_challenge
    challenge = get_daily_challenge()

    # Primer intento ya hecho por testuser en test anterior, usar nuevo usuario
    mock_det = make_mock_detector(
        detected_class=challenge.coco_name,
        confidence=0.75,
        bbox_ratio=0.25,
        others=2,
    )

    with patch("api.main.get_detector", return_value=mock_det):
        r = client.post("/submit", data={
            "username": "user_attempt2",
            "display_name": "Attempt User",
            "seconds_since_notification": 500,
            "attempt_number": 2,
        }, files={"photo": ("test.jpg", fake_image_bytes(), "image/jpeg")})

    assert r.status_code == 200
    data = r.json()
    assert data["attempt_penalty"] == 200
    print(f"  ✅ POST /submit (2º intento)  →  {data['total_score']} pts  penalización={data['attempt_penalty']}")


def test_get_leaderboard():
    r = client.get("/leaderboard")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert len(data["entries"]) >= 1  # Al menos testuser del test anterior
    top = data["entries"][0]
    assert top["rank"] == 1
    assert top["total_score"] >= 0
    print(f"  ✅ GET /leaderboard  →  {len(data['entries'])} usuarios, líder: {top['display_name']} ({top['total_score']} pts)")


def test_get_feed():
    r = client.get("/feed")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    print(f"  ✅ GET /feed  →  {len(data['entries'])} submissions hoy")


def test_get_user_stats():
    r = client.get("/user/testuser")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "testuser"
    assert data["total_score"] >= 0
    print(f"  ✅ GET /user/testuser  →  score={data['total_score']}, streak={data['current_streak']}")


def test_get_user_not_found():
    r = client.get("/user/nobody_xyz")
    assert r.status_code == 404
    print("  ✅ GET /user/nobody_xyz  →  404 Not Found")


# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_root,
        test_get_today,
        test_get_today_with_username,
        test_get_week,
        test_submit_correct_detection,
        test_submit_wrong_detection,
        test_submit_second_attempt,
        test_get_leaderboard,
        test_get_feed,
        test_get_user_stats,
        test_get_user_not_found,
    ]

    passed = 0
    print("\n🌐 API TESTS")
    for fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ❌ {fn.__name__}: {e}")

    print(f"\n{'─'*40}")
    print(f"  {passed}/{len(tests)} tests passed {'✅' if passed == len(tests) else '⚠️'}")
