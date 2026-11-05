"""Consulta financiera privada; el rol y el alcance se validan en servidor."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.reporte_financiero.schemas import Reporte
from app.modulos.reporte_financiero.servicio import obtener_reporte
from app.seguridad.permisos import requerir_cargos

router = APIRouter(prefix="/reportes", tags=["reporte financiero"])
Sesion = Annotated[Session, Depends(get_db)]
Cuenta = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "tesorero"))]


@router.get("/financiero", response_model=Reporte)
def financiero(
    desde: date,
    hasta: date,
    sesion: Sesion,
    actor: Cuenta,
    iglesia_id: Annotated[int | None, Query(gt=0)] = None,
):
    return obtener_reporte(sesion, actor, desde, hasta, iglesia_id)
