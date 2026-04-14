"""
database.py — SnapIT
Capa de datos con SQLite + SQLModel.
Tablas: User, DailySubmission, Friendship, SubmissionLike, SubmissionComment
Sin servidor, archivo local: snapit.db
"""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select

# ─── Modelos de base de datos ─────────────────────────────────────────────────

class User(SQLModel, table=True):
    id:              Optional[int] = Field(default=None, primary_key=True)
    username:        str           = Field(unique=True, index=True)
    display_name:    str
    created_at:      datetime      = Field(default_factory=datetime.utcnow)
    total_score:     int           = Field(default=0)
    current_streak:  int           = Field(default=0)
    max_streak:      int           = Field(default=0)
    # Auth — opcionales: guest no tiene email ni password
    email:           Optional[str] = Field(default=None, unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None)
    is_guest:        bool          = Field(default=True)
    is_active:       bool          = Field(default=True)
    push_token:      Optional[str] = Field(default=None)


class DailySubmission(SQLModel, table=True):
    id:               Optional[int] = Field(default=None, primary_key=True)
    user_id:          int           = Field(foreign_key="user.id", index=True)
    challenge_date:   date          = Field(index=True)

    # Objeto del reto
    target_coco_name: str
    target_display:   str

    # Resultado de la detección
    detected_class:   str
    confidence:       float
    bbox_area_ratio:  float
    other_detections: int
    correct:          bool

    # Tiempo
    seconds_since_notification: int
    attempt_number:   int         # Mejor de los 3 intentos

    # Puntuación
    total_score:      int
    base_score:       int
    speed_bonus:      int
    framing_bonus:    int
    clutter_penalty:  int
    attempt_penalty:  int
    speed_label:      str
    framing_label:    str

    # Imagen anotada (JPEG en base64, opcional)
    annotated_image_b64: Optional[str] = Field(default=None)

    submitted_at:     datetime = Field(default_factory=datetime.utcnow)


class Friendship(SQLModel, table=True):
    id:          Optional[int] = Field(default=None, primary_key=True)
    requester_id: int          = Field(foreign_key="user.id", index=True)
    receiver_id:  int          = Field(foreign_key="user.id", index=True)
    # pending → el receptor aún no ha aceptado | accepted → amigos
    status:      str           = Field(default="pending")   # "pending" | "accepted"
    created_at:  datetime      = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = Field(default=None)


class SubmissionLike(SQLModel, table=True):
    id:            Optional[int] = Field(default=None, primary_key=True)
    submission_id: int           = Field(foreign_key="dailysubmission.id", index=True)
    user_id:       int           = Field(foreign_key="user.id", index=True)
    created_at:    datetime      = Field(default_factory=datetime.utcnow)


class SubmissionComment(SQLModel, table=True):
    id:            Optional[int] = Field(default=None, primary_key=True)
    submission_id: int           = Field(foreign_key="dailysubmission.id", index=True)
    user_id:       int           = Field(foreign_key="user.id", index=True)
    text:          str           = Field(max_length=280)
    created_at:    datetime      = Field(default_factory=datetime.utcnow)


# ─── Engine y sesión ──────────────────────────────────────────────────────────

_DB_PATH = Path(__file__).parent.parent / "snapit.db"
_default_url = f"sqlite:///{_DB_PATH}"

# En producción se usa la variable DATABASE_URL (ej. Railway PostgreSQL).
# Railway expone la URL como postgres://, SQLAlchemy necesita postgresql://.
DATABASE_URL = os.getenv("DATABASE_URL", _default_url)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# connect_args solo válido para SQLite
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=_connect_args)


def create_db():
    """Crea las tablas si no existen y aplica migraciones pendientes."""
    SQLModel.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite"):
        _migrate()


def _migrate():
    """
    Añade columnas nuevas a tablas existentes sin borrar datos.
    SQLite no soporta ALTER TABLE para todo, pero sí ADD COLUMN.
    """
    migrations = [
        # Tabla user — columnas añadidas en Fase 4a (auth)
        ("user", "email",           "TEXT    DEFAULT NULL"),
        ("user", "hashed_password", "TEXT    DEFAULT NULL"),
        ("user", "is_guest",        "INTEGER DEFAULT 1"),
        ("user", "is_active",       "INTEGER DEFAULT 1"),
        ("user", "push_token",      "TEXT DEFAULT NULL"),
        # Tabla friendship — añadida en Fase 4b
        # (se crea entera con create_all, no necesita ADD COLUMN)
    ]

    with engine.connect() as conn:
        for table, column, col_def in migrations:
            try:
                conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE \"{table}\" ADD COLUMN \"{column}\" {col_def}"
                    )
                )
                conn.commit()
                print(f"  🔧 Migración: {table}.{column} añadida")
            except Exception:
                # La columna ya existe → ignorar silenciosamente
                pass


def get_session():
    """Generador de sesiones para FastAPI Depends."""
    with Session(engine) as session:
        yield session


# ─── Operaciones CRUD ─────────────────────────────────────────────────────────

def get_or_create_user(session: Session, username: str, display_name: str) -> User:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        user = User(username=username, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def get_user_submission_today(session: Session, user_id: int) -> Optional[DailySubmission]:
    today = date.today()
    return session.exec(
        select(DailySubmission)
        .where(DailySubmission.user_id == user_id)
        .where(DailySubmission.challenge_date == today)
    ).first()


def get_leaderboard(session: Session, limit: int = 10) -> list[User]:
    return session.exec(
        select(User).order_by(User.total_score.desc()).limit(limit)
    ).all()


def get_daily_feed(session: Session, challenge_date: Optional[date] = None, limit: int = 20) -> list[DailySubmission]:
    """Feed del día: todas las submissions de una fecha."""
    if challenge_date is None:
        challenge_date = date.today()
    return session.exec(
        select(DailySubmission)
        .where(DailySubmission.challenge_date == challenge_date)
        .order_by(DailySubmission.total_score.desc())
        .limit(limit)
    ).all()


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()


# ─── Friends CRUD ────────────────────────────────────────────────────────────

def get_friendship(session: Session, user_a_id: int, user_b_id: int) -> Optional[Friendship]:
    """Devuelve la amistad entre dos usuarios en cualquier dirección."""
    return session.exec(
        select(Friendship).where(
            ((Friendship.requester_id == user_a_id) & (Friendship.receiver_id == user_b_id)) |
            ((Friendship.requester_id == user_b_id) & (Friendship.receiver_id == user_a_id))
        )
    ).first()


def get_friends(session: Session, user_id: int) -> list[User]:
    """Lista de amigos aceptados."""
    friendships = session.exec(
        select(Friendship).where(
            ((Friendship.requester_id == user_id) | (Friendship.receiver_id == user_id)) &
            (Friendship.status == "accepted")
        )
    ).all()
    friend_ids = [
        f.receiver_id if f.requester_id == user_id else f.requester_id
        for f in friendships
    ]
    if not friend_ids:
        return []
    return session.exec(select(User).where(User.id.in_(friend_ids))).all()


def get_pending_requests(session: Session, user_id: int) -> list["FriendRequestInfo"]:
    """Solicitudes pendientes recibidas por user_id."""
    friendships = session.exec(
        select(Friendship).where(
            (Friendship.receiver_id == user_id) &
            (Friendship.status == "pending")
        )
    ).all()
    result = []
    for f in friendships:
        requester = session.get(User, f.requester_id)
        if requester:
            result.append({"friendship_id": f.id, "user": requester, "created_at": f.created_at})
    return result


def get_sent_requests(session: Session, user_id: int) -> list[User]:
    """Solicitudes enviadas pendientes."""
    friendships = session.exec(
        select(Friendship).where(
            (Friendship.requester_id == user_id) &
            (Friendship.status == "pending")
        )
    ).all()
    result = []
    for f in friendships:
        receiver = session.get(User, f.receiver_id)
        if receiver:
            result.append(receiver)
    return result


def get_friends_feed(session: Session, user_id: int, challenge_date: Optional[date] = None, limit: int = 30) -> list[DailySubmission]:
    """Feed filtrado: submissions de amigos + el propio usuario."""
    if challenge_date is None:
        challenge_date = date.today()
    friends = get_friends(session, user_id)
    friend_ids = [f.id for f in friends] + [user_id]
    return session.exec(
        select(DailySubmission)
        .where(DailySubmission.challenge_date == challenge_date)
        .where(DailySubmission.user_id.in_(friend_ids))
        .order_by(DailySubmission.total_score.desc())
        .limit(limit)
    ).all()


# ─── History CRUD ─────────────────────────────────────────────────────────────

def get_user_history(session: Session, user_id: int, limit: int = 30) -> list[DailySubmission]:
    """Historial de submissions de un usuario, más reciente primero."""
    return session.exec(
        select(DailySubmission)
        .where(DailySubmission.user_id == user_id)
        .order_by(DailySubmission.challenge_date.desc())
        .limit(limit)
    ).all()


# ─── Likes & Comments CRUD ───────────────────────────────────────────────────

def get_like(session: Session, submission_id: int, user_id: int) -> Optional[SubmissionLike]:
    return session.exec(
        select(SubmissionLike)
        .where(SubmissionLike.submission_id == submission_id)
        .where(SubmissionLike.user_id == user_id)
    ).first()


def count_likes(session: Session, submission_id: int) -> int:
    from sqlmodel import func
    result = session.exec(
        select(func.count(SubmissionLike.id))
        .where(SubmissionLike.submission_id == submission_id)
    ).one()
    return result or 0


def get_comments(session: Session, submission_id: int) -> list[SubmissionComment]:
    return session.exec(
        select(SubmissionComment)
        .where(SubmissionComment.submission_id == submission_id)
        .order_by(SubmissionComment.created_at.asc())
    ).all()


def count_comments(session: Session, submission_id: int) -> int:
    from sqlmodel import func
    result = session.exec(
        select(func.count(SubmissionComment.id))
        .where(SubmissionComment.submission_id == submission_id)
    ).one()
    return result or 0


def update_user_stats(session: Session, user: User, new_score: int, completed_dates: list[str]):
    """Actualiza score total y racha del usuario."""
    from core.challenge import get_streak_info
    streak_info = get_streak_info(completed_dates)
    user.total_score += new_score
    user.current_streak = streak_info["current_streak"]
    user.max_streak = max(user.max_streak, streak_info["max_streak"])
    session.add(user)
    session.commit()
    session.refresh(user)
