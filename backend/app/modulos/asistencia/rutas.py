"""Rutas de asistencia (#23)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modelos.listas import TIPOS_SERVICIO_ASISTENCIA
from app.modulos.asistencia.schemas import GuardarHoja, HojaRespuesta, hoy
from app.modulos.asistencia.servicio import guardar_hoja, obtener_hojas, obtener_usuario_actual

ETIQUETAS = {
    "fecha": "la fecha",
    "servicio": "el culto",
    "hoja": "la lista",
    "marcados": "las personas marcadas",
}


class RutaAsistencia(APIRoute):
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


router = APIRouter(prefix="/asistencia", tags=["asistencia"], route_class=RutaAsistencia)
Sesion = Annotated[Session, Depends(get_db)]
Actor = Annotated[Usuario, Depends(obtener_usuario_actual)]


@router.get("", response_model=list[HojaRespuesta])
def listar(sesion: Sesion, actor: Actor, fecha: date, servicio: str):
    if servicio not in TIPOS_SERVICIO_ASISTENCIA:
        raise HTTPException(status_code=422, detail="Culto no válido.")
    if fecha > hoy():
        raise HTTPException(status_code=422, detail="La fecha no puede ser futura.")
    return obtener_hojas(sesion, actor, fecha, servicio)


@router.put("", response_model=HojaRespuesta)
def guardar(datos: GuardarHoja, sesion: Sesion, actor: Actor):
    return guardar_hoja(sesion, actor, datos)
