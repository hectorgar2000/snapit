"""
auth.py — SnapIT
Lógica de autenticación: hashing de passwords y JWT tokens.

Flujo:
  Registro  → hash del password → guardar en BD → devolver JWT
  Login     → verificar hash → devolver JWT
  Petición  → extraer JWT del header → devolver User (o None si es guest)
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt as _bcrypt
import jwt as pyjwt
from jwt.exceptions import InvalidTokenError

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from api.database import get_session, get_user_by_username, User

# ── Configuración ─────────────────────────────────────────────────────────────

# En producción, usar una variable de entorno segura
SECRET_KEY  = os.getenv("SNAPIT_SECRET", "snapit-dev-secret-change-in-production-xyz987")
ALGORITHM   = "HS256"
TOKEN_EXPIRE_DAYS = 30

# oauth2_scheme con auto_error=False → permite peticiones sin token (guests)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {"sub": username, "exp": expire}
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """Devuelve el username del token, o None si es inválido/expirado."""
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except InvalidTokenError:
        return None


# ── Dependencias FastAPI ──────────────────────────────────────────────────────

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Optional[User]:
    """
    Dependencia opcional: devuelve el User si hay token válido, None si no.
    Permite que los endpoints funcionen tanto con usuario autenticado como guest.
    """
    if not token:
        return None
    username = decode_token(token)
    if not username:
        return None
    user = get_user_by_username(session, username)
    if not user or not user.is_active:
        return None
    return user


def require_auth(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Dependencia estricta: lanza 401 si no hay token válido.
    Para endpoints que sí requieren estar registrado (comentarios, likes, etc.)
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Necesitas iniciar sesión para esta acción",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
