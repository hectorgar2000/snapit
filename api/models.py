"""
models.py — SnapIT
Schemas Pydantic para requests y responses de la API.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Request schemas ──────────────────────────────────────────────────────────

class SubmitPhotoRequest(BaseModel):
    username:                   str
    display_name:               str = ""
    seconds_since_notification: int = Field(ge=0, description="Segundos desde la notificación")
    attempt_number:             int = Field(ge=1, le=3, description="Número de intento (1, 2 o 3)")
    # La imagen viene como multipart/form-data (ver endpoint), no aquí


# ─── Response schemas ─────────────────────────────────────────────────────────

class ChallengeResponse(BaseModel):
    date:          str
    weekday:       str
    object_name:   str
    object_emoji:  str
    difficulty:    str
    base_points:   int
    hint:          Optional[str]
    already_done:  bool  # Si el usuario ya completó el reto hoy


class ScoreResponse(BaseModel):
    correct:          bool
    detected_class:   str
    confidence_pct:   float
    total_score:      int

    # Desglose
    base_score:       int
    speed_bonus:      int
    framing_bonus:    int
    clutter_penalty:  int
    attempt_penalty:  int
    speed_label:      str
    framing_label:    str
    difficulty_mult:  float

    # Contexto
    attempt_number:   int
    seconds_elapsed:  int
    annotated_image_b64: Optional[str] = None  # JPEG anotado en base64


class UserStatsResponse(BaseModel):
    username:       str
    display_name:   str
    total_score:    int
    current_streak: int
    max_streak:     int


class LeaderboardEntry(BaseModel):
    rank:           int
    username:       str
    display_name:   str
    total_score:    int
    current_streak: int


class LeaderboardResponse(BaseModel):
    date:    str
    entries: list[LeaderboardEntry]


class FeedEntry(BaseModel):
    submission_id:  int
    username:       str
    display_name:   str
    object_emoji:   str
    object_name:    str
    total_score:    int
    confidence_pct: float
    speed_label:    str
    framing_label:  str
    correct:        bool
    submitted_at:   datetime
    annotated_image_b64: Optional[str] = None
    like_count:     int = 0
    comment_count:  int = 0
    user_liked:     bool = False


class FeedResponse(BaseModel):
    date:    str
    entries: list[FeedEntry]


class WeekPreviewDay(BaseModel):
    date:        str
    weekday:     str
    object_name: str
    object_emoji: str
    difficulty:  str
    is_today:    bool


class WeekPreviewResponse(BaseModel):
    week: list[WeekPreviewDay]


class ErrorResponse(BaseModel):
    error:   str
    detail:  Optional[str] = None


# ─── Auth schemas ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username:     str = Field(min_length=3, max_length=20, pattern=r'^[a-z0-9_]+$')
    display_name: str = Field(min_length=1, max_length=30)
    email:        str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password:     str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    username:     str
    display_name: str
    is_guest:     bool = False


class MeResponse(BaseModel):
    username:       str
    display_name:   str
    email:          Optional[str]
    is_guest:       bool
    total_score:    int
    current_streak: int
    max_streak:     int
    created_at:     datetime


# ─── Friends schemas ──────────────────────────────────────────────────────────

class FriendInfo(BaseModel):
    username:       str
    display_name:   str
    total_score:    int
    current_streak: int
    # Estado de la relación desde el punto de vista del que consulta
    status:         str   # "accepted" | "pending_sent" | "pending_received" | "none"


class FriendRequest(BaseModel):
    friendship_id: int
    username:      str
    display_name:  str
    created_at:    datetime


class FriendsResponse(BaseModel):
    friends:           list[FriendInfo]
    pending_received:  list[FriendRequest]   # Solicitudes que me han enviado
    pending_sent:      list[FriendInfo]       # Solicitudes que yo he enviado


# ─── Likes & Comments schemas ────────────────────────────────────────────────

class CommentEntry(BaseModel):
    id:           int
    username:     str
    display_name: str
    text:         str
    created_at:   datetime


class CommentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=280)


# ─── History schemas ──────────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    date:           str
    weekday:        str
    object_emoji:   str
    object_name:    str
    difficulty:     str
    correct:        bool
    total_score:    int
    confidence_pct: float
    attempt_number: int
    speed_label:    str
    framing_label:  str
    annotated_image_b64: Optional[str] = None


class HistoryResponse(BaseModel):
    username:       str
    display_name:   str
    total_score:    int
    current_streak: int
    max_streak:     int
    entries:        list[HistoryEntry]
    # Resumen de los últimos 30 días para el calendario
    calendar:       list[dict]   # [{date, score, correct}]
