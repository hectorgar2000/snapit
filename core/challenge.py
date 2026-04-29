"""
challenge.py — SnapIT
Gestiona el reto diario:
  - Qué objeto toca hoy (determinista por fecha, mismo objeto para todos)
  - Historial de retos pasados (sin repetir en X días)
  - Dificultad progresiva a lo largo de la semana
"""

import hashlib
from datetime import date, timedelta
from typing import Optional
from core.catalog import SnapObject, get_by_difficulty_active


# ─── Configuración ────────────────────────────────────────────────────────────

# Dificultad según día de la semana (0=Lunes … 6=Domingo)
WEEKDAY_DIFFICULTY = {
    0: "easy",    # Lunes
    1: "easy",    # Martes
    2: "medium",  # Miércoles
    3: "medium",  # Jueves
    4: "hard",    # Viernes
    5: "hard",    # Sábado
    6: "medium",  # Domingo — un respiro
}

SALT = "snapit_v1"  # Cambia esto para alterar la secuencia de retos


# ─── Función principal ────────────────────────────────────────────────────────

def get_daily_challenge(target_date: Optional[date] = None) -> SnapObject:
    """
    Devuelve el objeto del reto para una fecha dada.
    Determinista: la misma fecha siempre devuelve el mismo objeto.
    Todos los usuarios del mundo ven el mismo reto cada día (como Wordle).
    """
    if target_date is None:
        target_date = date.today()

    difficulty = WEEKDAY_DIFFICULTY[target_date.weekday()]
    pool = get_by_difficulty_active(difficulty)

    # Hash de la fecha → índice reproducible
    date_str = f"{SALT}:{target_date.isoformat()}"
    hash_int = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    index = hash_int % len(pool)

    return pool[index]


def get_week_preview(start_date: Optional[date] = None) -> list[dict]:
    """
    Devuelve el calendario de retos de la semana en curso.
    Útil para mostrar el calendario en la UI.
    """
    if start_date is None:
        # Lunes de la semana actual
        today = date.today()
        start_date = today - timedelta(days=today.weekday())

    week = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        challenge = get_daily_challenge(day)
        week.append({
            "date": day.isoformat(),
            "weekday": day.strftime("%A"),
            "object": challenge,
            "is_today": day == date.today(),
        })
    return week


def get_streak_info(completed_dates: list[str]) -> dict:
    """
    Calcula la racha actual y la racha máxima.
    completed_dates: lista de fechas ISO en las que el usuario completó el reto.
    """
    if not completed_dates:
        return {"current_streak": 0, "max_streak": 0, "last_completed": None}

    dates = sorted([date.fromisoformat(d) for d in completed_dates], reverse=True)
    today = date.today()

    # Racha actual
    current_streak = 0
    check_date = today
    date_set = set(dates)

    for _ in range(len(dates) + 1):
        if check_date in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Racha máxima
    max_streak = 0
    current = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1
    max_streak = max(max_streak, current_streak)

    return {
        "current_streak": current_streak,
        "max_streak": max_streak,
        "last_completed": dates[0].isoformat() if dates else None,
    }


# ─── Debug / test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    today = date.today()
    challenge = get_daily_challenge(today)

    print(f"\n🎯 Reto de hoy ({today.strftime('%A %d %B %Y')}):")
    print(f"   {challenge.emoji} {challenge.display_name}")
    print(f"   Dificultad: {challenge.difficulty.upper()}")
    print(f"   Puntos base: {challenge.base_points}")
    if challenge.hint:
        print(f"   Pista: {challenge.hint}")

    print("\n📅 Retos de esta semana:")
    for day_info in get_week_preview():
        marker = " ← HOY" if day_info["is_today"] else ""
        obj = day_info["object"]
        print(f"   {day_info['weekday'][:3]} {day_info['date']}  "
              f"{obj.emoji} {obj.display_name} ({obj.difficulty}){marker}")
