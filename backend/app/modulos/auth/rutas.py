"""Inicio de sesión JSON, descubierto automáticamente por main.py."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modulos.auth.schemas import EntradaLogin, RespuestaLogin
from app.modulos.auth.servicio import autenticar_usuario
from app.seguridad.tokens import crear_token


class RutaLogin(APIRoute):
    """Evita que los errores de validación devuelvan el cuerpo con la contraseña."""

    def get_route_handler(self):
        manejador = super().get_route_handler()

        async def validar_sin_exponer_datos(request: Request) -> Response:
            try:
                return await manejador(request)
            except RequestValidationError:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Envía usuario y contraseña como texto en un objeto JSON."},
                )

        return validar_sin_exponer_datos


router = APIRouter(prefix="/auth", tags=["autenticación"], route_class=RutaLogin)


@router.post("/login", response_model=RespuestaLogin)
def login(datos: EntradaLogin, sesion: Annotated[Session, Depends(get_db)]) -> RespuestaLogin:
    cuenta = autenticar_usuario(sesion, datos.usuario, datos.contrasena.get_secret_value())
    return RespuestaLogin(access_token=crear_token(str(cuenta.id)))
