"""Sesión actual y permisos por cargo, iglesia y grupo dirigido (D19, D20 y D21)."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos.grupos import Grupo
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
    sesion: Session,
    usuario: Usuario,
    iglesia_id: int | None,
    *,
    dinero: bool = False,
    area_id: int | None = None,
) -> None:
    """Validar con la iglesia REAL del recurso, cargado antes por el servicio.

    El área es un Grupo consultado en la base. Su iglesia y su líder se comprueban;
    enviar un area_id o una iglesia_id inventados no concede acceso. Los servicios
    deben cargar el recurso real y pasar aquí su iglesia y grupo antes de usarlo.
    """
    if dinero and usuario.cargo not in {"presbitero", "pastor", "tesorero"}:
        denegar()
    grupo = sesion.get(Grupo, area_id) if area_id is not None else None
    if area_id is not None:
        if grupo is None or (iglesia_id is not None and grupo.iglesia_id != iglesia_id):
            denegar()
        iglesia_id = grupo.iglesia_id
    if usuario.cargo == "presbitero":
        return
    if iglesia_id is None or usuario.iglesia_id != iglesia_id:
        denegar()
    if dinero or usuario.cargo in {"pastor", "apoyo_pastor"}:
        return
    if usuario.cargo == "tesorero":
        denegar()
    if (
        grupo is None
        or not grupo.activo
        or usuario.miembro_id is None
        or grupo.lider_miembro_id != usuario.miembro_id
    ):
        denegar()


def requerir_permiso(*cargos: str, dinero: bool = False, parametro_area: str = "area_id"):
    """Para rutas por iglesia_id y/o area_id (configurable); comprobar también el recurso.

    Lee el id de la ruta o de la consulta, pero nunca un cargo enviado por el cliente.
    Si el recurso se obtiene por otro id, usar validar_alcance con su iglesia real.
    """

    def dependencia(
        request: Request,
        usuario: Annotated[Usuario, Depends(obtener_usuario_actual)],
        sesion: Annotated[Session, Depends(get_db)],
    ) -> Usuario:
        if cargos and usuario.cargo not in cargos:
            denegar()

        def identificador(nombre: str) -> int | None:
            valor = request.path_params.get(nombre, request.query_params.get(nombre))
            if valor is None:
                return None
            try:
                numero = int(valor)
            except (TypeError, ValueError):
                denegar()
            if numero <= 0:
                denegar()
            return numero

        iglesia_id = identificador("iglesia_id")
        area_id = identificador(parametro_area)
        if iglesia_id is None and area_id is None:
            denegar()
        validar_alcance(sesion, usuario, iglesia_id, dinero=dinero, area_id=area_id)
        return usuario

    return dependencia
