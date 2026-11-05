"""Rutas de cuentas; /yo se registra antes de /{identificador}."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.usuarios.schemas import (
    UsuarioCambios,
    UsuarioNuevo,
    UsuarioRespuesta,
    UsuarioResumen,
)
from app.modulos.usuarios.servicio import (
    actualizar_cuenta,
    crear_cuenta,
    listar_cuentas,
    obtener_cuenta,
)
from app.seguridad.permisos import obtener_usuario_actual, requerir_cargos


class RutaUsuarios(APIRoute):
    """Los errores conservan campo y mensaje sin devolver contraseñas del cuerpo."""

    def get_route_handler(self):
        manejador = super().get_route_handler()

        async def validar(request: Request) -> Response:
            try:
                return await manejador(request)
            except RequestValidationError as error:
                errores = [
                    {"loc": e["loc"], "msg": "Dato de usuario no válido.", "type": e["type"]}
                    for e in error.errors()
                ]
                return JSONResponse(status_code=422, content={"detail": errores})

        return validar


router = APIRouter(prefix="/usuarios", tags=["usuarios"], route_class=RutaUsuarios)
Sesion = Annotated[Session, Depends(get_db)]
Gestor = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "apoyo_pastor"))]


@router.get("/yo", response_model=UsuarioRespuesta)
def yo(usuario: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Usuario:
    return usuario


@router.get("", response_model=list[UsuarioResumen])
def listar(sesion: Sesion, actor: Gestor):
    return listar_cuentas(sesion, actor)


@router.get("/{identificador}", response_model=UsuarioRespuesta)
def obtener(identificador: int, sesion: Sesion, actor: Gestor):
    return obtener_cuenta(sesion, actor, identificador)


@router.post("", response_model=UsuarioRespuesta, status_code=201)
def crear(datos: UsuarioNuevo, sesion: Sesion, actor: Gestor):
    return crear_cuenta(sesion, actor, datos)


@router.put("/{identificador}", response_model=UsuarioRespuesta)
def actualizar(identificador: int, datos: UsuarioCambios, sesion: Sesion, actor: Gestor):
    return actualizar_cuenta(sesion, actor, identificador, datos)
