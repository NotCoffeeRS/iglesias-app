"""Rutas de miembros (#17). `/buscar` usa el cuerpo para que ningún nombre viaje en la dirección."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Miembro, Usuario
from app.modelos.listas import ESTADOS_MIEMBRO
from app.modulos.miembros.schemas import (
    Busqueda,
    MiembroEntrada,
    MiembroRespuesta,
    MiembroResumen,
)
from app.modulos.miembros.servicio import (
    actualizar_miembro,
    consultar,
    crear_miembro,
    obtener_miembro,
    obtener_usuario_actual,
)

ETIQUETAS = {
    "nombre": "el nombre",
    "telefono": "el teléfono",
    "correo": "el correo",
    "fecha_nacimiento": "la fecha de nacimiento",
    "direccion": "la dirección",
    "estado_civil": "el estado civil",
    "fecha_bautizo": "la fecha de bautizo",
    "fecha_ingreso": "la fecha de ingreso",
    "iglesia_id": "la iglesia",
    "estado": "el estado",
    "texto": "el texto a buscar",
}


class RutaMiembros(APIRoute):
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


router = APIRouter(prefix="/miembros", tags=["miembros"], route_class=RutaMiembros)
Sesion = Annotated[Session, Depends(get_db)]
Actor = Annotated[Usuario, Depends(obtener_usuario_actual)]


@router.get("", response_model=list[MiembroResumen])
def listar(
    sesion: Sesion,
    actor: Actor,
    estado: str | None = None,
    iglesia_id: Annotated[int | None, Query(gt=0)] = None,
):
    if estado is not None and estado not in ESTADOS_MIEMBRO:
        raise HTTPException(status_code=422, detail="Estado no válido.")
    return consultar(sesion, actor, estado=estado, iglesia_id=iglesia_id)


@router.post("/buscar", response_model=list[MiembroResumen])
def buscar(datos: Busqueda, sesion: Sesion, actor: Actor):
    return consultar(
        sesion, actor, estado=datos.estado, iglesia_id=datos.iglesia_id, texto=datos.texto
    )


@router.get("/{identificador}", response_model=MiembroRespuesta)
def obtener(identificador: int, sesion: Sesion, actor: Actor) -> Miembro:
    return obtener_miembro(sesion, actor, identificador)


@router.post("", response_model=MiembroRespuesta, status_code=201)
def crear(datos: MiembroEntrada, sesion: Sesion, actor: Actor) -> Miembro:
    return crear_miembro(sesion, actor, datos)


@router.put("/{identificador}", response_model=MiembroRespuesta)
def actualizar(identificador: int, datos: MiembroEntrada, sesion: Sesion, actor: Actor) -> Miembro:
    return actualizar_miembro(sesion, actor, identificador, datos)
