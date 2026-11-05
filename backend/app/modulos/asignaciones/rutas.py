"""Consulta de grupos propios, alta por gestores y retiro sin borrar miembros."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.asignaciones.schemas import (
    AsignacionEntrada,
    AsignacionRespuesta,
    GrupoOpcion,
    MiembroOpcion,
)
from app.modulos.asignaciones.servicio import (
    asignar,
    candidatos,
    integrantes,
    listar_grupos,
    quitar,
)
from app.seguridad.permisos import obtener_usuario_actual, requerir_cargos

router = APIRouter(prefix="/asignaciones", tags=["asignaciones"])
Sesion = Annotated[Session, Depends(get_db)]
Cuenta = Annotated[Usuario, Depends(obtener_usuario_actual)]
Gestor = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "apoyo_pastor"))]


@router.get("/grupos", response_model=list[GrupoOpcion])
def grupos(sesion: Sesion, actor: Cuenta):
    return listar_grupos(sesion, actor)


@router.get("/{grupo_id}", response_model=list[MiembroOpcion])
def miembros(grupo_id: int, sesion: Sesion, actor: Cuenta):
    return integrantes(sesion, actor, grupo_id)


@router.get("/{grupo_id}/candidatos", response_model=list[MiembroOpcion])
def disponibles(grupo_id: int, sesion: Sesion, actor: Gestor):
    return candidatos(sesion, actor, grupo_id)


@router.post("", response_model=AsignacionRespuesta, status_code=201)
def crear(datos: AsignacionEntrada, sesion: Sesion, actor: Gestor):
    return asignar(sesion, actor, datos.grupo_id, datos.miembro_id)


@router.delete("/{grupo_id}/{miembro_id}", status_code=204)
def eliminar(grupo_id: int, miembro_id: int, sesion: Sesion, actor: Cuenta):
    quitar(sesion, actor, grupo_id, miembro_id)
    return Response(status_code=204)
