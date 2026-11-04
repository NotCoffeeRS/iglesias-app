"""Autenticación contra el modelo Usuario del #4."""

import secrets

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modelos.usuarios import Usuario
from app.seguridad.contrasenas import crear_hash, verificar_contrasena

# La cuenta inexistente también comprueba un hash para reducir diferencias de tiempo.
_HASH_FICTICIO = crear_hash(secrets.token_urlsafe(32))


def autenticar_usuario(sesion: Session, usuario: str, contrasena: str) -> Usuario:
    cuenta = sesion.scalar(
        select(Usuario).where(func.lower(Usuario.nombre_usuario) == func.lower(usuario))
    )
    hash_guardado = cuenta.contrasena_hash if cuenta is not None else _HASH_FICTICIO
    contrasena_valida = verificar_contrasena(contrasena, hash_guardado)
    if cuenta is None or not contrasena_valida or not cuenta.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return cuenta
