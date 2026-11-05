"""Rutas de grupos (#20)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modelos.listas import TIPOS_GRUPO
from app.modulos.grupos.schemas import GrupoEntrada, GrupoRespuesta, GrupoResumen
from app.modulos.grupos.servicio import (
    actualizar_grupo,
    crear_grupo,
    listar_grupos,
    obtener_grupo,
)
from app.seguridad.permisos import obtener_usuario_actual

ETIQUETAS = {
    "nombre": "el nombre",
    "tipo": "el tipo",
    "iglesia_id": "la iglesia",
    "lider_id": "el líder",
    "asistente_id": "el asistente",
}


class RutaGrupos(APIRoute):
    """Los errores de validación dicen qué campo revisar sin repetir lo que se recibió."""

    def get_route_handler(self):
        manejador = super().get_route_handler()

        async def validar(request: Request) -> Response:
            try:
                return await manejador(request)
            except RequestValidationError as error:
                errores = []
                for e in error.errors():
                    campo = e["loc"][-1] if e["loc"] else ""
                    if e["type"] == "extra_forbidden":
                        mensaje = "Ese dato no se guarda."
                    elif campo in ETIQUETAS:
                        mensaje = f"Revisa {ETIQUETAS[campo]}."
                    else:
                        mensaje = "Dato no válido."
                    errores.append({"loc": e["loc"], "msg": mensaje, "type": e["type"]})
                return JSONResponse(status_code=422, content={"detail": errores})

        return validar


router = APIRouter(prefix="/grupos", tags=["grupos"], route_class=RutaGrupos)
Sesion = Annotated[Session, Depends(get_db)]
Actor = Annotated[Usuario, Depends(obtener_usuario_actual)]


@router.get("", response_model=list[GrupoResumen])
def listar(sesion: Sesion, actor: Actor, tipo: str | None = None):
    if tipo is not None and tipo not in TIPOS_GRUPO:
        raise HTTPException(status_code=422, detail="Tipo no válido.")
    return listar_grupos(sesion, actor, tipo)


@router.get("/{identificador}", response_model=GrupoRespuesta)
def obtener(identificador: int, sesion: Sesion, actor: Actor):
    return obtener_grupo(sesion, actor, identificador)


@router.post("", response_model=GrupoRespuesta, status_code=201)
def crear(datos: GrupoEntrada, sesion: Sesion, actor: Actor):
    return crear_grupo(sesion, actor, datos)


@router.put("/{identificador}", response_model=GrupoRespuesta)
def actualizar(identificador: int, datos: GrupoEntrada, sesion: Sesion, actor: Actor):
    return actualizar_grupo(sesion, actor, identificador, datos)
