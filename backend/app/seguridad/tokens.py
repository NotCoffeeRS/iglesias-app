"""Tokens de acceso firmados; los permisos se consultarán en el servidor (#9)."""

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITMO = "HS256"
DURACION_TOKEN = timedelta(minutes=30)
_bearer = HTTPBearer(auto_error=False)


def _obtener_clave() -> str:
    clave = os.environ.get("SECRET_KEY", "")
    if len(clave.encode("utf-8")) < 32:
        raise RuntimeError("Configura SECRET_KEY con un secreto aleatorio de al menos 32 bytes")
    return clave


def _sesion_invalida() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión no válida o vencida",
        headers={"WWW-Authenticate": "Bearer"},
    )


def crear_token(usuario_id: str) -> str:
    """Usa el identificador interno como sub, sin nombres ni permisos en el token."""
    if not isinstance(usuario_id, str) or not usuario_id.strip():
        raise ValueError("El identificador de usuario debe ser un texto no vacío")
    ahora = datetime.now(UTC)
    return jwt.encode(
        {"sub": usuario_id, "iat": ahora, "exp": ahora + DURACION_TOKEN},
        _obtener_clave(),
        algorithm=ALGORITMO,
    )


def validar_token(token: str) -> str:
    """Exige firma HS256 y las tres declaraciones; rechaza sesiones vencidas con 401."""
    clave = _obtener_clave()
    try:
        contenido = jwt.decode(
            token,
            clave,
            algorithms=[ALGORITMO],
            options={"require": ["sub", "iat", "exp"]},
        )
        sujeto = contenido["sub"]
        if not isinstance(sujeto, str) or not sujeto.strip():
            raise jwt.InvalidTokenError()
        return sujeto
    except jwt.InvalidTokenError:
        raise _sesion_invalida() from None


def obtener_usuario_id(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    """Dependencia Bearer. Validar la cuenta y su alcance corresponde a la capa de usuarios."""
    if credenciales is None:
        raise _sesion_invalida()
    return validar_token(credenciales.credentials)
