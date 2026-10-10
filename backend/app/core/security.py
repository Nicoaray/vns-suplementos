from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import settings

# Se usa bcrypt directamente (en vez de passlib, que esta practicamente
# sin mantenimiento) y PyJWT (en vez de python-jose, que tuvo varios CVEs
# de confusion de algoritmo sin resolver). Son las librerias que
# recomienda hoy la comunidad de FastAPI para este tipo de proyecto.


def hash_password(plain_password: str) -> str:
    # bcrypt trunca en 72 bytes; validamos el largo en el schema de
    # entrada (UserCreate) para que esto nunca ocurra en la practica.
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: dict = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    # Se fija explicitamente el algoritmo permitido (HS256) tanto al
    # firmar como al validar, para evitar ataques de confusion de
    # algoritmo (ej. un token manipulado que pida usar "none").
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except InvalidTokenError:
        return None
