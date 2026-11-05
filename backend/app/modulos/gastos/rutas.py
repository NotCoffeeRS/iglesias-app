"""Contrato de gastos: listado, alta y anulación sin borrado."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.gastos.schemas import Anulacion, GastoNuevo, GastoRespuesta
from app.modulos.gastos.servicio import anular_gasto, listar_gastos, registrar_gasto
from app.seguridad.permisos import requerir_cargos


class RutaGastos(APIRoute):
    """No refleja montos, notas ni motivos del cuerpo al fallar la validación."""

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
                            {"loc": e["loc"], "msg": "Dato de gasto no válido.", "type": e["type"]}
                            for e in error.errors()
                        ]
                    },
                )

        return validar


router = APIRouter(prefix="/gastos", tags=["gastos"], route_class=RutaGastos)
Sesion = Annotated[Session, Depends(get_db)]
Cuenta = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "tesorero"))]


@router.get("", response_model=list[GastoRespuesta])
def listar(
    desde: date,
    hasta: date,
    sesion: Sesion,
    actor: Cuenta,
    iglesia_id: Annotated[int | None, Query(gt=0)] = None,
):
    return listar_gastos(sesion, actor, desde, hasta, iglesia_id)


@router.post("", response_model=GastoRespuesta, status_code=201)
def registrar(datos: GastoNuevo, sesion: Sesion, actor: Cuenta):
    return registrar_gasto(sesion, actor, datos)


@router.post("/{identificador}/anular", response_model=GastoRespuesta)
def anular(identificador: int, datos: Anulacion, sesion: Sesion, actor: Cuenta):
    return anular_gasto(sesion, actor, identificador, datos.motivo)
