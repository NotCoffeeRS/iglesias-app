"""Consulta privada de marcas guardadas por periodo e iglesia."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.reporte_asistencia.schemas import Reporte
from app.modulos.reporte_asistencia.servicio import obtener_reporte
from app.seguridad.permisos import obtener_usuario_actual

router = APIRouter(prefix="/reportes", tags=["reporte de asistencia"])


@router.get("/asistencia", response_model=Reporte)
def reporte(
    desde: date,
    hasta: date,
    sesion: Annotated[Session, Depends(get_db)],
    actor: Annotated[Usuario, Depends(obtener_usuario_actual)],
    iglesia_id: Annotated[int | None, Query(gt=0)] = None,
    servicio: str | None = None,
):
    return obtener_reporte(sesion, actor, desde, hasta, iglesia_id, servicio)
