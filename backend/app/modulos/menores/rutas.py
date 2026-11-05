"""Rutas privadas de menores; los datos personales nunca se reflejan en errores."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.menores.schemas import MenorEntrada, MenorRespuesta, MenorResumen
from app.modulos.menores.servicio import (
    actualizar_menor,
    crear_menor,
    listar_menores,
    obtener_menor,
    respuesta,
)
from app.seguridad.permisos import requerir_cargos


class RutaMenores(APIRoute):
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
                                "msg": "Revisa los datos del menor y sus tutores.",
                                "type": e["type"],
                            }
                            for e in error.errors()
                        ]
                    },
                )

        return validar


router = APIRouter(prefix="/menores", tags=["menores"], route_class=RutaMenores)
Sesion = Annotated[Session, Depends(get_db)]
Gestor = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "apoyo_pastor"))]


@router.get("", response_model=list[MenorResumen])
def listar(sesion: Sesion, actor: Gestor, iglesia_id: Annotated[int | None, Query(gt=0)] = None):
    return listar_menores(sesion, actor, iglesia_id)


@router.get("/{identificador}", response_model=MenorRespuesta)
def obtener(identificador: int, sesion: Sesion, actor: Gestor):
    return respuesta(sesion, obtener_menor(sesion, actor, identificador))


@router.post("", response_model=MenorRespuesta, status_code=201)
def crear(datos: MenorEntrada, sesion: Sesion, actor: Gestor):
    return crear_menor(sesion, actor, datos)


@router.put("/{identificador}", response_model=MenorRespuesta)
def actualizar(identificador: int, datos: MenorEntrada, sesion: Sesion, actor: Gestor):
    return actualizar_menor(sesion, actor, identificador, datos)
