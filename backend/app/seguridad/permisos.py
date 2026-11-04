"""Sesión actual y permisos por cargo/iglesia (D19 y D20, Issue #9).

El alcance por área espera la decisión de Marcos. Los cargos de área no obtienen
acceso general a una iglesia como alternativa: se deniega hasta resolver su vínculo.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos.usuarios import Usuario
from app.seguridad.tokens import obtener_usuario_id


def denegar() -> None:
    raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")


def obtener_usuario_actual(
    sujeto: Annotated[str, Depends(obtener_usuario_id)],
    sesion: Annotated[Session, Depends(get_db)],
) -> Usuario:
    try:
        identificador = int(sujeto)
    except ValueError:
        identificador = 0
    usuario = sesion.get(Usuario, identificador) if identificador > 0 else None
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=401,
            detail="Sesión no válida o vencida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def requerir_cargos(*cargos: str):
    """Dependencia que siempre lee de la base la cuenta activa y su cargo actual."""

    def dependencia(usuario: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Usuario:
        if usuario.cargo not in cargos:
            denegar()
        return usuario

    return dependencia


def validar_alcance(
    usuario: Usuario, iglesia_id: int | None, *, dinero: bool = False, area_id: int | None = None
) -> None:
    """Validar con la iglesia REAL del recurso, cargado antes por el servicio.

    El pastor y el presbítero abarcan su iglesia/todas. El apoyo no ve dinero;
    el tesorero solo entra en recursos financieros de su iglesia. Los demás cargos
    requieren el vínculo de área pendiente; area_id por sí solo no otorga acceso.
    """
    if dinero and usuario.cargo not in {"presbitero", "pastor", "tesorero"}:
        denegar()
    if usuario.cargo == "presbitero":
        return
    if iglesia_id is None or usuario.iglesia_id != iglesia_id:
        denegar()
    if dinero or usuario.cargo in {"pastor", "apoyo_pastor"}:
        return
    denegar()


def requerir_permiso(*cargos: str, dinero: bool = False):
    """Para rutas por iglesia_id; el servicio valida además el recurso concreto.

    Lee el id de la ruta o de la consulta, pero nunca un cargo enviado por el cliente.
    Si el recurso se obtiene por otro id, usar validar_alcance con su iglesia real.
    """

    def dependencia(
        request: Request, usuario: Annotated[Usuario, Depends(obtener_usuario_actual)]
    ) -> Usuario:
        if cargos and usuario.cargo not in cargos:
            denegar()
        valor = request.path_params.get("iglesia_id", request.query_params.get("iglesia_id"))
        try:
            iglesia_id = int(valor)
        except (TypeError, ValueError):
            denegar()
        if iglesia_id <= 0:
            denegar()
        validar_alcance(usuario, iglesia_id, dinero=dinero)
        return usuario

    return dependencia
