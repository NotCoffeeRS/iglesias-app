"""Comunicados: lista de vigentes, detalle, publicación y edición (descubierto por main.py)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.modulos.comunicados import servicio
from app.modulos.comunicados.schemas import ComunicadoEntrada, ComunicadoSalida
from app.seguridad.tokens import obtener_usuario_id

router = APIRouter(prefix="/comunicados", tags=["comunicados"])

Sesion = Annotated[Session, Depends(get_db)]
UsuarioId = Annotated[str, Depends(obtener_usuario_id)]


@router.get("", response_model=list[ComunicadoSalida])
def listar(sesion: Sesion, usuario_id: UsuarioId) -> list[ComunicadoSalida]:
    """Solo los comunicados vigentes que tu cargo puede ver."""
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.listar(sesion, usuario)


@router.get("/{comunicado_id}", response_model=ComunicadoSalida)
def obtener(comunicado_id: int, sesion: Sesion, usuario_id: UsuarioId) -> ComunicadoSalida:
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.obtener(sesion, usuario, comunicado_id)


@router.post("", response_model=ComunicadoSalida, status_code=201)
def publicar(datos: ComunicadoEntrada, sesion: Sesion, usuario_id: UsuarioId) -> ComunicadoSalida:
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.publicar(sesion, usuario, datos)


@router.put("/{comunicado_id}", response_model=ComunicadoSalida)
def editar(
    comunicado_id: int, datos: ComunicadoEntrada, sesion: Sesion, usuario_id: UsuarioId
) -> ComunicadoSalida:
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.editar(sesion, usuario, comunicado_id, datos)
