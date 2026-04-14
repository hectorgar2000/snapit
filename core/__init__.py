# SnapIT Core Engine
from core.detector import get_detector, DetectionResult, Detection
from core.scorer import calculate_score, DetectionInput, ScoreBreakdown
from core.catalog import CATALOG, get_by_coco_name, SnapObject
from core.challenge import get_daily_challenge, get_week_preview, get_streak_info

__all__ = [
    "get_detector", "DetectionResult", "Detection",
    "calculate_score", "DetectionInput", "ScoreBreakdown",
    "CATALOG", "get_by_coco_name", "SnapObject",
    "get_daily_challenge", "get_week_preview", "get_streak_info",
]
