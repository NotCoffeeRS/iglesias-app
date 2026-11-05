"""Eventos: lista, detalle, alta, edición y cancelación (descubierto por main.py)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.modulos.eventos import servicio
from app.modulos.eventos.schemas import EventoEntrada, EventoSalida
from app.seguridad.tokens import obtener_usuario_id

router = APIRouter(prefix="/eventos", tags=["eventos"])

Sesion = Annotated[Session, Depends(get_db)]
UsuarioId = Annotated[str, Depends(obtener_usuario_id)]


@router.get("", response_model=list[EventoSalida])
def listar(
    sesion: Sesion,
    usuario_id: UsuarioId,
    desde: date | None = None,
    iglesia_id: int | None = None,
) -> list[EventoSalida]:
    """Eventos de `desde` (por defecto hoy) en adelante; incluye los cancelados, marcados."""
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.listar(sesion, usuario, desde, iglesia_id)


@router.get("/{evento_id}", response_model=EventoSalida)
def obtener(evento_id: int, sesion: Sesion, usuario_id: UsuarioId) -> EventoSalida:
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.obtener(sesion, usuario, evento_id)


@router.post("", response_model=EventoSalida, status_code=201)
def crear(datos: EventoEntrada, sesion: Sesion, usuario_id: UsuarioId) -> EventoSalida:
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.crear(sesion, usuario, datos)


@router.put("/{evento_id}", response_model=EventoSalida)
def editar(
    evento_id: int, datos: EventoEntrada, sesion: Sesion, usuario_id: UsuarioId
) -> EventoSalida:
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.editar(sesion, usuario, evento_id, datos)


@router.post("/{evento_id}/cancelar", response_model=EventoSalida)
def cancelar(evento_id: int, sesion: Sesion, usuario_id: UsuarioId) -> EventoSalida:
    """Un evento no se borra: queda marcado como cancelado."""
    usuario = servicio.usuario_actual(sesion, usuario_id)
    return servicio.cancelar(sesion, usuario, evento_id)
