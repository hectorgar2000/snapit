"""
main.py — SnapIT API
FastAPI backend con 5 endpoints principales.

Arrancar con:
    cd snapit
    uvicorn api.main:app --reload --port 8000

Docs interactivas: http://localhost:8000/docs
"""

import base64
import sys
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from time import time
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from api.database import (
    create_db, get_session,
    get_or_create_user, get_user_submission_today,
    get_leaderboard, get_daily_feed, update_user_stats,
    get_user_by_email, get_user_by_username,
    get_friendship, get_friends, get_pending_requests,
    get_sent_requests, get_friends_feed, get_user_history,
    get_like, count_likes, get_comments, count_comments,
    DailySubmission, User, Friendship, SubmissionLike, SubmissionComment,
)
from api.models import (
    ChallengeResponse, ScoreResponse, UserStatsResponse,
    LeaderboardResponse, LeaderboardEntry,
    FeedResponse, FeedEntry,
    WeekPreviewResponse, WeekPreviewDay,
    ErrorResponse,
    RegisterRequest, LoginRequest, TokenResponse, MeResponse,
    ChangePasswordRequest, DeleteAccountRequest, PushTokenRequest,
    FriendInfo, FriendRequest, FriendsResponse,
    HistoryEntry, HistoryResponse,
    CommentEntry, CommentRequest,
)
from api.auth import (
    hash_password, verify_password,
    create_access_token,
    get_current_user, require_auth,
)
from core.challenge import get_daily_challenge, get_week_preview
from core.detector import get_detector
from core.scorer import calculate_score, DetectionInput
from core.catalog import get_by_coco_name


# ─── Rate limiting (in-memory, por IP) ───────────────────────────────────────

_rate_buckets: dict[str, list[float]] = defaultdict(list)

def _check_rate(ip: str, limit: int, window: int = 60) -> None:
    """Lanza 429 si la IP supera `limit` peticiones en `window` segundos."""
    now = time()
    bucket = _rate_buckets[ip]
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Demasiadas peticiones. Espera {window} segundos e inténtalo de nuevo."
        )
    bucket.append(now)


# ─── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SnapIT API",
    description="Backend para SnapIT — el juego diario de detección de objetos con YOLO",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],  # "null" = origen file://
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.on_event("startup")
def on_startup():
    create_db()
    # Montar el frontend como archivos estáticos
    frontend_dir = Path(__file__).parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    print("✅ SnapIT API arrancada — base de datos lista")


# Servir el frontend en la raíz (evita CORS cuando se abre como file://)
@app.get("/app", include_in_schema=False)
def serve_frontend():
    frontend = Path(__file__).parent.parent / "frontend" / "index.html"
    return FileResponse(str(frontend))

# PWA — deben estar en la raíz para que el scope del SW cubra /app
@app.get("/manifest.json", include_in_schema=False)
def serve_manifest():
    f = Path(__file__).parent.parent / "frontend" / "manifest.json"
    return FileResponse(str(f), media_type="application/manifest+json")

@app.get("/sw.js", include_in_schema=False)
def serve_sw():
    f = Path(__file__).parent.parent / "frontend" / "sw.js"
    return FileResponse(str(f), media_type="application/javascript")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "SnapIT", "version": "0.2.0"}



# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.post("/register", response_model=TokenResponse, tags=["Auth"])
def register(request: Request, body: RegisterRequest, session: Session = Depends(get_session)):
    _check_rate(request.client.host, limit=5, window=60)  # 5 registros/min por IP
    """
    Registro de nuevo usuario con email y contraseña.
    Devuelve un JWT token listo para usar.
    """
    # Username único
    if get_user_by_username(session, body.username):
        raise HTTPException(status_code=409, detail="Ese nombre de usuario ya está en uso")

    # Email único
    if get_user_by_email(session, body.email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email")

    user = User(
        username=body.username,
        display_name=body.display_name,
        email=body.email,
        hashed_password=hash_password(body.password),
        is_guest=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        username=user.username,
        display_name=user.display_name,
        is_guest=False,
    )


@app.post("/login", response_model=TokenResponse, tags=["Auth"])
def login(body: LoginRequest, session: Session = Depends(get_session)):
    """Login con email y contraseña. Devuelve JWT token."""
    user = get_user_by_email(session, body.email)

    if not user or user.is_guest or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        username=user.username,
        display_name=user.display_name,
        is_guest=False,
    )


@app.get("/me", response_model=MeResponse, tags=["Auth"])
def me(current_user: User = Depends(require_auth)):
    """Devuelve los datos del usuario autenticado."""
    return MeResponse(
        username=current_user.username,
        display_name=current_user.display_name,
        email=current_user.email,
        is_guest=current_user.is_guest,
        total_score=current_user.total_score,
        current_streak=current_user.current_streak,
        max_streak=current_user.max_streak,
        created_at=current_user.created_at,
    )


@app.post("/guest", response_model=TokenResponse, tags=["Auth"])
def create_guest(
    username: str,
    display_name: str = "",
    session: Session = Depends(get_session),
):
    """
    Crea o recupera un usuario guest (sin contraseña).
    Permite jugar sin registrarse, pero la cuenta no persiste entre dispositivos.
    """
    if not display_name:
        display_name = username

    user = get_or_create_user(session, username, display_name)

    # Si ya es usuario registrado, no degradar a guest
    if not user.is_guest:
        token = create_access_token(user.username)
        return TokenResponse(
            access_token=token,
            username=user.username,
            display_name=user.display_name,
            is_guest=False,
        )

    token = create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        username=user.username,
        display_name=user.display_name,
        is_guest=True,
    )


@app.get("/today", response_model=ChallengeResponse, tags=["Challenge"])
def get_today_challenge(
    username: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Devuelve el reto del día.
    Si hay token JWT (o ?username=xxx) indica si ya lo completó hoy.
    """
    challenge = get_daily_challenge()
    already_done = False

    # Preferir el usuario del token sobre el query param
    user = current_user
    if not user and username:
        user = session.exec(select(User).where(User.username == username)).first()

    if user:
        sub = get_user_submission_today(session, user.id)
        already_done = sub is not None

    return ChallengeResponse(
        date=date.today().isoformat(),
        weekday=date.today().strftime("%A"),
        object_name=challenge.display_name,
        object_emoji=challenge.emoji,
        difficulty=challenge.difficulty,
        base_points=challenge.base_points,
        hint=challenge.hint,
        already_done=already_done,
    )


@app.get("/week", response_model=WeekPreviewResponse, tags=["Challenge"])
def get_week():
    """Devuelve los retos de toda la semana actual."""
    week_data = get_week_preview()
    return WeekPreviewResponse(
        week=[
            WeekPreviewDay(
                date=d["date"],
                weekday=d["weekday"],
                object_name=d["object"].display_name,
                object_emoji=d["object"].emoji,
                difficulty=d["object"].difficulty,
                is_today=d["is_today"],
            )
            for d in week_data
        ]
    )


@app.post("/submit", response_model=ScoreResponse, tags=["Submission"])
async def submit_photo(
    request:                    Request,
    username:                   str  = Form(...),
    display_name:               str  = Form(""),
    seconds_since_notification: int  = Form(...),
    attempt_number:             int  = Form(...),
    photo:                      UploadFile = File(...),
    session:                    Session = Depends(get_session),
    current_user:               Optional[User] = Depends(get_current_user),
):
    """
    Sube una foto y recibe la puntuación.

    - Acepta hasta 3 intentos por día.
    - Guarda solo la mejor puntuación.
    - Devuelve el score con desglose completo e imagen anotada.
    """
    _check_rate(request.client.host, limit=15, window=60)  # 15 fotos/min por IP

    # Validaciones básicas
    if attempt_number not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="attempt_number debe ser 1, 2 o 3")

    content_type = photo.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    # Usuario: preferir el del token JWT sobre el form param
    if current_user:
        user = current_user
    else:
        if not display_name:
            display_name = username
        user = get_or_create_user(session, username, display_name)

    # Comprobar si ya tiene una submission hoy con mayor puntuación
    existing = get_user_submission_today(session, user.id)
    if existing and attempt_number <= existing.attempt_number:
        raise HTTPException(
            status_code=409,
            detail=f"Ya tienes una submission hoy (intento {existing.attempt_number}). "
                   f"Usa attempt_number > {existing.attempt_number} para mejorarla."
        )

    # Leer imagen
    image_bytes = await photo.read()

    # Reto del día
    challenge = get_daily_challenge()

    # Detección YOLO
    try:
        detector = get_detector()
        detection_result = detector.analyze(image_bytes, challenge.coco_name)
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Motor de detección no disponible: {e}. "
                   f"Instala ultralytics con: pip install ultralytics"
        )

    # Preparar datos para el scorer
    if detection_result.target_detection:
        td = detection_result.target_detection
        detected_class = td.class_name
        confidence = td.confidence
        bbox_area_ratio = td.bbox_area_ratio
    else:
        # No se detectó el objeto objetivo — buscamos si se detectó algo
        detected_class = (
            detection_result.all_detections[0].class_name
            if detection_result.all_detections else "nothing"
        )
        confidence = (
            detection_result.all_detections[0].confidence
            if detection_result.all_detections else 0.0
        )
        bbox_area_ratio = 0.0

    other_detections = len([
        d for d in detection_result.all_detections
        if d.class_name != challenge.coco_name
    ])

    score_input = DetectionInput(
        target_object=challenge,
        detected_class=detected_class,
        confidence=confidence,
        bbox_area_ratio=bbox_area_ratio,
        other_detections=other_detections,
        seconds_since_notification=seconds_since_notification,
        attempt_number=attempt_number,
    )
    score = calculate_score(score_input)

    # Imagen anotada en base64
    annotated_b64 = None
    if detection_result.annotated_image:
        annotated_b64 = base64.b64encode(detection_result.annotated_image).decode()

    # Guardar o actualizar submission
    if existing:
        # Actualizar solo si la nueva puntuación es mejor
        if score.total_score > existing.total_score:
            score_diff = score.total_score - existing.total_score
            _update_submission(existing, challenge, detected_class, confidence,
                               bbox_area_ratio, other_detections, score,
                               seconds_since_notification, attempt_number, annotated_b64)
            session.add(existing)
            session.commit()
            # Actualizar stats del usuario con la diferencia
            user.total_score += score_diff
            session.add(user)
            session.commit()
    else:
        # Primera submission del día
        sub = DailySubmission(
            user_id=user.id,
            challenge_date=date.today(),
            target_coco_name=challenge.coco_name,
            target_display=challenge.display_name,
            detected_class=detected_class,
            confidence=confidence,
            bbox_area_ratio=bbox_area_ratio,
            other_detections=other_detections,
            correct=score.correct,
            seconds_since_notification=seconds_since_notification,
            attempt_number=attempt_number,
            total_score=score.total_score,
            base_score=score.base_score,
            speed_bonus=score.speed_bonus,
            framing_bonus=score.framing_bonus,
            clutter_penalty=score.clutter_penalty,
            attempt_penalty=score.attempt_penalty,
            speed_label=score.speed_label,
            framing_label=score.framing_label,
            annotated_image_b64=annotated_b64,
        )
        session.add(sub)
        session.commit()

        # Calcular racha actualizada — .all() devuelve objetos Row, extraemos el valor
        all_rows = session.exec(
            select(DailySubmission.challenge_date)
            .where(DailySubmission.user_id == user.id)
        ).all()
        completed_dates = [str(r) if not hasattr(r, '__iter__') else str(r[0])
                           for r in all_rows]
        update_user_stats(session, user, score.total_score, completed_dates)

    return ScoreResponse(
        correct=score.correct,
        detected_class=detected_class,
        confidence_pct=score.confidence_pct,
        total_score=score.total_score,
        base_score=score.base_score,
        speed_bonus=score.speed_bonus,
        framing_bonus=score.framing_bonus,
        clutter_penalty=score.clutter_penalty,
        attempt_penalty=score.attempt_penalty,
        speed_label=score.speed_label,
        framing_label=score.framing_label,
        difficulty_mult=score.difficulty_mult,
        attempt_number=attempt_number,
        seconds_elapsed=seconds_since_notification,
        annotated_image_b64=annotated_b64,
    )


@app.get("/leaderboard", response_model=LeaderboardResponse, tags=["Social"])
def leaderboard(
    limit: int = 10,
    session: Session = Depends(get_session),
):
    """Top usuarios por puntuación total acumulada."""
    users = get_leaderboard(session, limit)
    return LeaderboardResponse(
        date=date.today().isoformat(),
        entries=[
            LeaderboardEntry(
                rank=i + 1,
                username=u.username,
                display_name=u.display_name,
                total_score=u.total_score,
                current_streak=u.current_streak,
            )
            for i, u in enumerate(users)
        ],
    )


@app.get("/user/{username}/history", response_model=HistoryResponse, tags=["User"])
def get_history(
    username: str,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Historial de submissions de un usuario (últimos 30 días)."""
    user = get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")

    can_see_images = False
    if current_user:
        if current_user.id == user.id:
            can_see_images = True
        else:
            friendship = get_friendship(session, current_user.id, user.id)
            can_see_images = friendship is not None and friendship.status == "accepted"

    submissions = get_user_history(session, user.id)
    entries = []
    calendar = []
    for sub in submissions:
        obj = get_by_coco_name(sub.target_coco_name)
        emoji = obj.emoji if obj else "📦"
        difficulty = obj.difficulty if obj else "easy"
        entries.append(HistoryEntry(
            date=sub.challenge_date.isoformat(),
            weekday=sub.challenge_date.strftime("%A"),
            object_emoji=emoji,
            object_name=sub.target_display,
            difficulty=difficulty,
            correct=sub.correct,
            total_score=sub.total_score,
            confidence_pct=round(sub.confidence * 100, 1),
            attempt_number=sub.attempt_number,
            speed_label=sub.speed_label,
            framing_label=sub.framing_label,
            annotated_image_b64=sub.annotated_image_b64 if can_see_images else None,
        ))
        calendar.append({"date": sub.challenge_date.isoformat(),
                         "score": sub.total_score, "correct": sub.correct})

    return HistoryResponse(
        username=user.username, display_name=user.display_name,
        total_score=user.total_score, current_streak=user.current_streak,
        max_streak=user.max_streak, entries=entries, calendar=calendar,
    )


@app.get("/user/{username}", response_model=UserStatsResponse, tags=["User"])
def get_user_stats(username: str, session: Session = Depends(get_session)):
    """Estadísticas públicas de un usuario."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")
    return UserStatsResponse(
        username=user.username,
        display_name=user.display_name,
        total_score=user.total_score,
        current_streak=user.current_streak,
        max_streak=user.max_streak,
    )


# ── Friends endpoints ─────────────────────────────────────────────────────────

@app.get("/friends", response_model=FriendsResponse, tags=["Friends"])
def list_friends(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Lista de amigos, solicitudes recibidas y enviadas del usuario autenticado."""
    friends = get_friends(session, current_user.id)
    pending_recv = get_pending_requests(session, current_user.id)
    pending_sent = get_sent_requests(session, current_user.id)

    return FriendsResponse(
        friends=[
            FriendInfo(username=f.username, display_name=f.display_name,
                       total_score=f.total_score, current_streak=f.current_streak,
                       status="accepted")
            for f in friends
        ],
        pending_received=[
            FriendRequest(friendship_id=r["friendship_id"], username=r["user"].username,
                          display_name=r["user"].display_name, created_at=r["created_at"])
            for r in pending_recv
        ],
        pending_sent=[
            FriendInfo(username=u.username, display_name=u.display_name,
                       total_score=u.total_score, current_streak=u.current_streak,
                       status="pending_sent")
            for u in pending_sent
        ],
    )


@app.post("/friends/{username}", tags=["Friends"])
def send_friend_request(
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Envía una solicitud de amistad a otro usuario."""
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="No puedes añadirte a ti mismo")

    target = get_user_by_username(session, username)
    if not target:
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")

    existing = get_friendship(session, current_user.id, target.id)
    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=409, detail="Ya sois amigos")
        raise HTTPException(status_code=409, detail="Ya existe una solicitud pendiente")

    friendship = Friendship(requester_id=current_user.id, receiver_id=target.id)
    session.add(friendship)
    session.commit()
    return {"message": f"Solicitud enviada a {target.display_name}"}


@app.post("/friends/{username}/accept", tags=["Friends"])
def accept_friend_request(
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Acepta una solicitud de amistad recibida."""
    requester = get_user_by_username(session, username)
    if not requester:
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")

    friendship = session.exec(
        select(Friendship).where(
            (Friendship.requester_id == requester.id) &
            (Friendship.receiver_id == current_user.id) &
            (Friendship.status == "pending")
        )
    ).first()

    if not friendship:
        raise HTTPException(status_code=404, detail="No hay solicitud pendiente de ese usuario")

    friendship.status = "accepted"
    friendship.accepted_at = datetime.utcnow()
    session.add(friendship)
    session.commit()
    return {"message": f"Ahora eres amigo de {requester.display_name}"}


@app.delete("/friends/{username}", tags=["Friends"])
def remove_friend(
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Elimina un amigo o cancela una solicitud pendiente."""
    other = get_user_by_username(session, username)
    if not other:
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")

    friendship = get_friendship(session, current_user.id, other.id)
    if not friendship:
        raise HTTPException(status_code=404, detail="No existe relación con ese usuario")

    session.delete(friendship)
    session.commit()
    return {"message": f"Relación con {other.display_name} eliminada"}


@app.get("/friends/search", tags=["Friends"])
def search_users(
    q: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Busca usuarios por username o display_name (mínimo 3 caracteres)."""
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Introduce al menos 3 caracteres")

    users = session.exec(
        select(User).where(
            (User.username.contains(q)) | (User.display_name.contains(q))
        ).limit(10)
    ).all()

    results = []
    for u in users:
        if u.id == current_user.id:
            continue
        existing = get_friendship(session, current_user.id, u.id)
        status = "none"
        if existing:
            if existing.status == "accepted":
                status = "accepted"
            elif existing.requester_id == current_user.id:
                status = "pending_sent"
            else:
                status = "pending_received"
        results.append(FriendInfo(
            username=u.username, display_name=u.display_name,
            total_score=u.total_score, current_streak=u.current_streak,
            status=status,
        ))
    return results


# ── Feed actualizado (con opción friends-only) ────────────────────────────────

@app.get("/feed", response_model=FeedResponse, tags=["Social"])
def daily_feed(
    friends_only: bool = False,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Feed del día. Con ?friends_only=true muestra solo amigos (requiere auth)."""
    challenge = get_daily_challenge()

    if friends_only and current_user:
        submissions = get_friends_feed(session, current_user.id)
    else:
        submissions = get_daily_feed(session)

    entries = []
    for sub in submissions:
        user = session.get(User, sub.user_id)
        if not user:
            continue
        lcount = count_likes(session, sub.id)
        ccount = count_comments(session, sub.id)
        u_liked = False
        if current_user:
            u_liked = get_like(session, sub.id, current_user.id) is not None
        entries.append(FeedEntry(
            submission_id=sub.id,
            username=user.username,
            display_name=user.display_name,
            object_emoji=challenge.emoji,
            object_name=sub.target_display,
            total_score=sub.total_score,
            confidence_pct=round(sub.confidence * 100, 1),
            speed_label=sub.speed_label,
            framing_label=sub.framing_label,
            correct=sub.correct,
            submitted_at=sub.submitted_at,
            annotated_image_b64=sub.annotated_image_b64,
            like_count=lcount,
            comment_count=ccount,
            user_liked=u_liked,
        ))

    return FeedResponse(date=date.today().isoformat(), entries=entries)


@app.patch("/me/profile", response_model=MeResponse, tags=["Auth"])
def update_profile(
    display_name: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Actualiza el display name del usuario autenticado."""
    if display_name:
        current_user.display_name = display_name
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
    return MeResponse(
        username=current_user.username,
        display_name=current_user.display_name,
        email=current_user.email,
        is_guest=current_user.is_guest,
        total_score=current_user.total_score,
        current_streak=current_user.current_streak,
        max_streak=current_user.max_streak,
        created_at=current_user.created_at,
    )


@app.post("/me/password", tags=["Auth"])
def change_password(
    body: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Cambia la contraseña del usuario autenticado."""
    if current_user.is_guest or not current_user.hashed_password:
        raise HTTPException(status_code=400, detail="Los usuarios invitados no tienen contraseña")
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    current_user.hashed_password = hash_password(body.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Contraseña actualizada correctamente"}


@app.delete("/me", tags=["Auth"])
def delete_account(
    body: DeleteAccountRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Elimina la cuenta del usuario autenticado de forma permanente."""
    if not current_user.is_guest:
        if not current_user.hashed_password or not verify_password(body.password, current_user.hashed_password):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    # Borrar datos del usuario
    submissions = session.exec(select(DailySubmission).where(DailySubmission.user_id == current_user.id)).all()
    for s in submissions:
        likes = session.exec(select(SubmissionLike).where(SubmissionLike.submission_id == s.id)).all()
        comments = session.exec(select(SubmissionComment).where(SubmissionComment.submission_id == s.id)).all()
        for l in likes: session.delete(l)
        for c in comments: session.delete(c)
        session.delete(s)
    friendships = session.exec(
        select(Friendship).where(
            (Friendship.requester_id == current_user.id) | (Friendship.receiver_id == current_user.id)
        )
    ).all()
    for f in friendships: session.delete(f)
    likes_given = session.exec(select(SubmissionLike).where(SubmissionLike.user_id == current_user.id)).all()
    comments_given = session.exec(select(SubmissionComment).where(SubmissionComment.user_id == current_user.id)).all()
    for l in likes_given: session.delete(l)
    for c in comments_given: session.delete(c)
    session.delete(current_user)
    session.commit()
    return {"message": "Cuenta eliminada correctamente"}


@app.post("/me/push-token", tags=["Auth"])
def save_push_token(
    body: PushTokenRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Guarda el token de notificaciones push del dispositivo."""
    current_user.push_token = body.token
    session.add(current_user)
    session.commit()
    return {"message": "Token guardado"}


# ── Likes & Comentarios ───────────────────────────────────────────────────────

@app.post("/submission/{sid}/like", tags=["Social"])
def like_submission(
    sid: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Da like a una submission. Idempotente: no falla si ya existe."""
    sub = session.get(DailySubmission, sid)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission no encontrada")
    if not get_like(session, sid, current_user.id):
        session.add(SubmissionLike(submission_id=sid, user_id=current_user.id))
        session.commit()
    return {"likes": count_likes(session, sid)}


@app.delete("/submission/{sid}/like", tags=["Social"])
def unlike_submission(
    sid: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Quita el like de una submission."""
    like = get_like(session, sid, current_user.id)
    if like:
        session.delete(like)
        session.commit()
    return {"likes": count_likes(session, sid)}


@app.get("/submission/{sid}/comments", response_model=list[CommentEntry], tags=["Social"])
def list_comments(sid: int, session: Session = Depends(get_session)):
    """Lista los comentarios de una submission."""
    if not session.get(DailySubmission, sid):
        raise HTTPException(status_code=404, detail="Submission no encontrada")
    comments = get_comments(session, sid)
    result = []
    for c in comments:
        u = session.get(User, c.user_id)
        if u:
            result.append(CommentEntry(
                id=c.id, username=u.username, display_name=u.display_name,
                text=c.text, created_at=c.created_at,
            ))
    return result


@app.post("/submission/{sid}/comments", response_model=CommentEntry, tags=["Social"])
def add_comment(
    sid: int,
    body: CommentRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """Añade un comentario a una submission."""
    if not session.get(DailySubmission, sid):
        raise HTTPException(status_code=404, detail="Submission no encontrada")
    comment = SubmissionComment(submission_id=sid, user_id=current_user.id, text=body.text.strip())
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return CommentEntry(
        id=comment.id, username=current_user.username,
        display_name=current_user.display_name,
        text=comment.text, created_at=comment.created_at,
    )


# ─── Helper privado ───────────────────────────────────────────────────────────

def _update_submission(sub, challenge, detected_class, confidence,
                        bbox_area_ratio, other_detections, score,
                        seconds, attempt, annotated_b64):
    sub.detected_class = detected_class
    sub.confidence = confidence
    sub.bbox_area_ratio = bbox_area_ratio
    sub.other_detections = other_detections
    sub.correct = score.correct
    sub.seconds_since_notification = seconds
    sub.attempt_number = attempt
    sub.total_score = score.total_score
    sub.base_score = score.base_score
    sub.speed_bonus = score.speed_bonus
    sub.framing_bonus = score.framing_bonus
    sub.clutter_penalty = score.clutter_penalty
    sub.attempt_penalty = score.attempt_penalty
    sub.speed_label = score.speed_label
    sub.framing_label = score.framing_label
    if annotated_b64:
        sub.annotated_image_b64 = annotated_b64
