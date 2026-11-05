"""Rutas privadas de iglesias; ubicaciones públicas corresponden al #14."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.iglesias.schemas import IglesiaEntrada, IglesiaRespuesta, IglesiaResumen
from app.modulos.iglesias.servicio import (
    actualizar_iglesia,
    crear_iglesia,
    listar_iglesias,
    obtener_iglesia,
)
from app.seguridad.permisos import obtener_usuario_actual, requerir_cargos


class RutaIglesias(APIRoute):
    """Evita devolver teléfonos personales en errores de validación."""

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
                                "msg": "Dato de iglesia no válido.",
                                "type": e["type"],
                            }
                            for e in error.errors()
                        ]
                    },
                )

        return validar


router = APIRouter(prefix="/iglesias", tags=["iglesias"], route_class=RutaIglesias)
Sesion = Annotated[Session, Depends(get_db)]
Cuenta = Annotated[Usuario, Depends(obtener_usuario_actual)]
Editor = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "apoyo_pastor"))]
Presbitero = Annotated[Usuario, Depends(requerir_cargos("presbitero"))]


@router.get("", response_model=list[IglesiaResumen])
def listar(sesion: Sesion, actor: Cuenta):
    return listar_iglesias(sesion, actor)


@router.get("/{identificador}", response_model=IglesiaRespuesta)
def obtener(identificador: int, sesion: Sesion, actor: Cuenta):
    return obtener_iglesia(sesion, actor, identificador)


@router.post("", response_model=IglesiaRespuesta, status_code=201)
def crear(datos: IglesiaEntrada, sesion: Sesion, actor: Presbitero):
    return crear_iglesia(sesion, actor, datos)


@router.put("/{identificador}", response_model=IglesiaRespuesta)
def actualizar(identificador: int, datos: IglesiaEntrada, sesion: Sesion, actor: Editor):
    return actualizar_iglesia(sesion, actor, identificador, datos)
