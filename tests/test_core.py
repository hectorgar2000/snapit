"""
test_core.py — SnapIT
Tests del core engine sin necesidad de modelo YOLO real.
Testea catalog, scorer y challenge de forma aislada.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from core.catalog import get_by_coco_name, get_by_difficulty, all_coco_names, CATALOG
from core.scorer import calculate_score, DetectionInput
from core.challenge import get_daily_challenge, get_week_preview, get_streak_info


# ─── Test catalog ─────────────────────────────────────────────────────────────

def test_catalog_loaded():
    assert len(CATALOG) > 0, "El catálogo no puede estar vacío"
    print(f"  ✅ Catálogo cargado: {len(CATALOG)} objetos")

def test_catalog_lookup():
    chair = get_by_coco_name("chair")
    assert chair is not None
    assert chair.coco_name == "chair"
    assert chair.difficulty == "easy"
    print(f"  ✅ Lookup por COCO name: {chair.display_name} ({chair.emoji})")

def test_catalog_filter():
    easy = get_by_difficulty("easy")
    medium = get_by_difficulty("medium")
    hard = get_by_difficulty("hard")
    assert len(easy) > 0
    assert len(medium) > 0
    assert len(hard) > 0
    print(f"  ✅ Filtro por dificultad: easy={len(easy)}, medium={len(medium)}, hard={len(hard)}")

def test_catalog_no_missing_coco_names():
    names = all_coco_names()
    assert len(names) == len(set(names)), "Hay nombres COCO duplicados"
    print(f"  ✅ Sin duplicados: {len(names)} nombres únicos")


# ─── Test scorer ──────────────────────────────────────────────────────────────

def test_score_correct_detection():
    chair = get_by_coco_name("chair")
    data = DetectionInput(
        target_object=chair,
        detected_class="chair",
        confidence=0.92,
        bbox_area_ratio=0.45,
        other_detections=0,
        seconds_since_notification=60,
        attempt_number=1,
    )
    result = calculate_score(data)
    assert result.correct == True
    assert result.total_score > 0
    assert result.speed_bonus == 500    # < 2 min = lightning
    assert result.framing_bonus == 300  # > 40% = perfect
    assert result.attempt_penalty == 0
    print(f"  ✅ Score correcto 1er intento: {result.total_score} pts "
          f"(base={result.base_score}, speed=+{result.speed_bonus}, framing=+{result.framing_bonus})")

def test_score_wrong_detection():
    chair = get_by_coco_name("chair")
    data = DetectionInput(
        target_object=chair,
        detected_class="car",   # Objeto incorrecto
        confidence=0.99,
        bbox_area_ratio=0.80,
        other_detections=0,
        seconds_since_notification=30,
        attempt_number=1,
    )
    result = calculate_score(data)
    assert result.correct == False
    assert result.total_score == 0
    print(f"  ✅ Score incorrecto → 0 pts")

def test_score_second_attempt_penalty():
    chair = get_by_coco_name("chair")
    data = DetectionInput(
        target_object=chair,
        detected_class="chair",
        confidence=0.85,
        bbox_area_ratio=0.30,
        other_detections=1,
        seconds_since_notification=400,
        attempt_number=2,
    )
    result = calculate_score(data)
    assert result.attempt_penalty == 200
    print(f"  ✅ Penalización 2º intento: -{result.attempt_penalty} pts → total={result.total_score}")

def test_score_hard_multiplier():
    dog = get_by_coco_name("dog")
    data = DetectionInput(
        target_object=dog,
        detected_class="dog",
        confidence=0.80,
        bbox_area_ratio=0.35,
        other_detections=0,
        seconds_since_notification=200,
        attempt_number=1,
    )
    result = calculate_score(data)
    assert result.difficulty_mult == 2.0  # Hard = ×2
    print(f"  ✅ Multiplicador HARD (×2): {result.total_score} pts")

def test_score_clutter_penalty():
    chair = get_by_coco_name("chair")
    data = DetectionInput(
        target_object=chair,
        detected_class="chair",
        confidence=0.90,
        bbox_area_ratio=0.40,
        other_detections=6,     # Escena muy cargada
        seconds_since_notification=300,
        attempt_number=1,
    )
    result = calculate_score(data)
    assert result.clutter_penalty == 300  # Máximo (6 × 50 = 300, cap en 300)
    print(f"  ✅ Penalización clutter máxima: -{result.clutter_penalty} pts")


# ─── Test challenge ───────────────────────────────────────────────────────────

def test_challenge_today():
    challenge = get_daily_challenge()
    assert challenge is not None
    assert challenge.coco_name in [obj.coco_name for obj in CATALOG]
    print(f"  ✅ Reto de hoy: {challenge.emoji} {challenge.display_name} ({challenge.difficulty})")

def test_challenge_deterministic():
    d = date(2025, 6, 15)
    c1 = get_daily_challenge(d)
    c2 = get_daily_challenge(d)
    assert c1.coco_name == c2.coco_name, "El reto debe ser determinista para la misma fecha"
    print(f"  ✅ Determinista: misma fecha → mismo objeto ({c1.display_name})")

def test_challenge_different_dates():
    d1 = date(2025, 6, 15)
    d2 = date(2025, 6, 16)
    c1 = get_daily_challenge(d1)
    c2 = get_daily_challenge(d2)
    print(f"  ✅ Fechas distintas: {c1.display_name} vs {c2.display_name}")

def test_week_preview():
    week = get_week_preview()
    assert len(week) == 7
    print(f"  ✅ Semana completa: {[d['object'].emoji for d in week]}")

def test_streak_empty():
    info = get_streak_info([])
    assert info["current_streak"] == 0
    print(f"  ✅ Racha vacía: {info}")

def test_streak_consecutive():
    today = date.today()
    from datetime import timedelta
    dates = [(today - timedelta(days=i)).isoformat() for i in range(5)]
    info = get_streak_info(dates)
    assert info["current_streak"] == 5
    print(f"  ✅ Racha de 5 días: {info['current_streak']} (max={info['max_streak']})")


# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("📦 CATALOG", [
            test_catalog_loaded,
            test_catalog_lookup,
            test_catalog_filter,
            test_catalog_no_missing_coco_names,
        ]),
        ("🎯 SCORER", [
            test_score_correct_detection,
            test_score_wrong_detection,
            test_score_second_attempt_penalty,
            test_score_hard_multiplier,
            test_score_clutter_penalty,
        ]),
        ("📅 CHALLENGE", [
            test_challenge_today,
            test_challenge_deterministic,
            test_challenge_different_dates,
            test_week_preview,
            test_streak_empty,
            test_streak_consecutive,
        ]),
    ]

    total = 0
    passed = 0
    for group_name, group_tests in tests:
        print(f"\n{group_name}")
        for test_fn in group_tests:
            total += 1
            try:
                test_fn()
                passed += 1
            except Exception as e:
                print(f"  ❌ {test_fn.__name__}: {e}")

    print(f"\n{'─'*40}")
    print(f"  {passed}/{total} tests passed {'✅' if passed == total else '⚠️'}")
