"""
scorer.py — SnapIT
Fórmula de puntuación completa.

Factores:
  1. Confidence score    → base del score (0–100%)
  2. Dificultad          → multiplicador según easy/medium/hard
  3. Velocidad           → bonus por responder rápido tras la notificación
  4. Encuadre            → bonus si el objeto ocupa suficiente área del frame
  5. Limpieza            → penalización si hay muchos otros objetos detectados
  6. Intento             → penalización si no es el primer intento (2º o 3º)
"""

from dataclasses import dataclass
from typing import Optional
from core.catalog import SnapObject


# ─── Configuración de bonuses y multiplicadores ───────────────────────────────

DIFFICULTY_MULTIPLIER = {
    "easy":   1.0,
    "medium": 1.5,
    "hard":   2.0,
}

SPEED_BONUS = {
    # Segundos desde la notificación → bonus extra
    "lightning": (0,    120,  500),   # < 2 min   → +500
    "fast":      (120,  300,  300),   # 2–5 min   → +300
    "normal":    (300,  900,  100),   # 5–15 min  → +100
    "slow":      (900,  None, 0),     # > 15 min  → +0
}

FRAMING_THRESHOLDS = {
    "perfect":  (0.40, 300),   # bbox ocupa >40% del frame → +300
    "good":     (0.20, 150),   # bbox ocupa 20–40%         → +150
    "poor":     (0.05, 0),     # bbox ocupa 5–20%          → +0
    "tiny":     (0.00, -100),  # bbox ocupa <5%            → -100
}

CLUTTER_PENALTY_PER_OBJECT = 50   # Penalización por cada objeto extra detectado
MAX_CLUTTER_PENALTY = 300         # Máximo de penalización por clutter

ATTEMPT_PENALTY = {
    1: 0,     # Primer intento   → sin penalización
    2: -200,  # Segundo intento  → -200
    3: -400,  # Tercer intento   → -400
}

MAX_SCORE = 9999
MIN_SCORE = 0


# ─── Dataclasses de entrada/salida ───────────────────────────────────────────

@dataclass
class DetectionInput:
    """Datos que llegan del detector para calcular el score."""
    target_object: SnapObject       # Objeto del reto del día
    detected_class: str             # Clase detectada por YOLO (puede ser distinta al objetivo)
    confidence: float               # 0.0 – 1.0
    bbox_area_ratio: float          # Área del bbox / área total del frame (0.0 – 1.0)
    other_detections: int           # Nº de otros objetos detectados en la misma foto
    seconds_since_notification: int # Segundos desde que se recibió la notificación
    attempt_number: int             # 1, 2 o 3


@dataclass
class ScoreBreakdown:
    """Desglose completo de la puntuación."""
    # ¿Se detectó el objeto correcto?
    correct: bool

    # Puntuación base
    base_score: int           # base_points del catálogo × confidence × difficulty_mult
    confidence_pct: float     # Porcentaje de confianza (0–100)

    # Bonuses y penalizaciones
    speed_bonus: int
    framing_bonus: int
    clutter_penalty: int
    attempt_penalty: int

    # Total
    total_score: int

    # Metadatos para mostrar
    speed_label: str          # "⚡ Lightning", "🚀 Fast", etc.
    framing_label: str        # "🎯 Perfect", "👍 Good", etc.
    difficulty_mult: float


# ─── Función principal ────────────────────────────────────────────────────────

def calculate_score(data: DetectionInput) -> ScoreBreakdown:
    """
    Calcula la puntuación completa de una foto enviada.
    Devuelve ScoreBreakdown con todos los componentes.
    """
    # 1. ¿Se detectó el objeto correcto?
    correct = (data.detected_class == data.target_object.coco_name)

    if not correct:
        # Si no se detectó el objeto correcto, puntuación 0
        return ScoreBreakdown(
            correct=False,
            base_score=0,
            confidence_pct=round(data.confidence * 100, 1),
            speed_bonus=0,
            framing_bonus=0,
            clutter_penalty=0,
            attempt_penalty=0,
            total_score=0,
            speed_label="❌ Not detected",
            framing_label="—",
            difficulty_mult=1.0,
        )

    # 2. Score base = base_points × confidence × difficulty_multiplier
    diff_mult = DIFFICULTY_MULTIPLIER.get(data.target_object.difficulty, 1.0)
    base_score = int(data.target_object.base_points * data.confidence * diff_mult)

    # 3. Speed bonus
    speed_bonus, speed_label = _speed_bonus(data.seconds_since_notification)

    # 4. Framing bonus
    framing_bonus, framing_label = _framing_bonus(data.bbox_area_ratio)

    # 5. Clutter penalty
    clutter_penalty = min(
        data.other_detections * CLUTTER_PENALTY_PER_OBJECT,
        MAX_CLUTTER_PENALTY
    )

    # 6. Attempt penalty
    attempt_penalty = abs(ATTEMPT_PENALTY.get(data.attempt_number, -400))

    # 7. Total
    total = base_score + speed_bonus + framing_bonus - clutter_penalty - attempt_penalty
    total = max(MIN_SCORE, min(MAX_SCORE, total))

    return ScoreBreakdown(
        correct=True,
        base_score=base_score,
        confidence_pct=round(data.confidence * 100, 1),
        speed_bonus=speed_bonus,
        framing_bonus=framing_bonus,
        clutter_penalty=clutter_penalty,
        attempt_penalty=attempt_penalty,
        total_score=total,
        speed_label=speed_label,
        framing_label=framing_label,
        difficulty_mult=diff_mult,
    )


# ─── Helpers privados ─────────────────────────────────────────────────────────

def _speed_bonus(seconds: int) -> tuple[int, str]:
    labels = {
        "lightning": "⚡ Lightning",
        "fast":      "🚀 Fast",
        "normal":    "🕐 Normal",
        "slow":      "🐢 Slow",
    }
    for key, (lo, hi, bonus) in SPEED_BONUS.items():
        if hi is None or seconds < hi:
            if seconds >= lo:
                return bonus, labels[key]
    return 0, "🐢 Slow"


def _framing_bonus(area_ratio: float) -> tuple[int, str]:
    if area_ratio >= FRAMING_THRESHOLDS["perfect"][0]:
        return FRAMING_THRESHOLDS["perfect"][1], "🎯 Perfect framing"
    elif area_ratio >= FRAMING_THRESHOLDS["good"][0]:
        return FRAMING_THRESHOLDS["good"][1], "👍 Good framing"
    elif area_ratio >= FRAMING_THRESHOLDS["poor"][0]:
        return FRAMING_THRESHOLDS["poor"][1], "📷 Acceptable"
    else:
        return FRAMING_THRESHOLDS["tiny"][1], "🔍 Too small"


# ─── Debug / test rápido ──────────────────────────────────────────────────────

if __name__ == "__main__":
    from core.catalog import get_by_coco_name

    chair = get_by_coco_name("chair")

    test = DetectionInput(
        target_object=chair,
        detected_class="chair",
        confidence=0.91,
        bbox_area_ratio=0.45,
        other_detections=2,
        seconds_since_notification=180,
        attempt_number=1,
    )

    result = calculate_score(test)
    print("\n── SnapIT Score Breakdown ──")
    print(f"  Correcto:        {'✅' if result.correct else '❌'}")
    print(f"  Confianza:       {result.confidence_pct}%")
    print(f"  Score base:      {result.base_score}")
    print(f"  Velocidad:       {result.speed_label}  (+{result.speed_bonus})")
    print(f"  Encuadre:        {result.framing_label}  (+{result.framing_bonus})")
    print(f"  Clutter:         -{result.clutter_penalty}")
    print(f"  Intento:         -{result.attempt_penalty}")
    print(f"  ─────────────────────────")
    print(f"  TOTAL:           {result.total_score} pts")
