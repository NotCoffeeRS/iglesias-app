"""Consulta, registro por partidas y anulación; no hay borrado ni datos de donantes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.ingresos.schemas import Anulacion, IngresoRespuesta, IngresosNuevos
from app.modulos.ingresos.servicio import anular_ingreso, listar_ingresos, registrar_ingresos
from app.seguridad.permisos import requerir_cargos


class RutaIngresos(APIRoute):
    """Los errores no reflejan montos, motivos ni descripciones del cuerpo."""

    def get_route_handler(self):
        manejador = super().get_route_handler()

        async def validar(request: Request) -> Response:
            try:
                return await manejador(request)
            except RequestValidationError as error:
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": [
                            {
                                "loc": e["loc"],
                                "msg": "Dato de ingreso no válido.",
                                "type": e["type"],
                            }
                            for e in error.errors()
                        ]
                    },
                )

        return validar


router = APIRouter(prefix="/ingresos", tags=["ingresos"], route_class=RutaIngresos)
Sesion = Annotated[Session, Depends(get_db)]
Cuenta = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "tesorero"))]


@router.get("", response_model=list[IngresoRespuesta])
def listar(
    desde: date,
    hasta: date,
    sesion: Sesion,
    actor: Cuenta,
    iglesia_id: Annotated[int | None, Query(gt=0)] = None,
):
    return listar_ingresos(sesion, actor, desde, hasta, iglesia_id)


@router.post("", response_model=list[IngresoRespuesta], status_code=201)
def registrar(datos: IngresosNuevos, sesion: Sesion, actor: Cuenta):
    return registrar_ingresos(sesion, actor, datos)


@router.post("/{identificador}/anular", response_model=IngresoRespuesta)
def anular(identificador: int, datos: Anulacion, sesion: Sesion, actor: Cuenta):
    return anular_ingreso(sesion, actor, identificador, datos.motivo)
