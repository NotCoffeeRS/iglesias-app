"""Contrato de gestión de horarios y consulta pública acordado con el frontend."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Usuario
from app.modulos.horarios.schemas import (
    HorarioEntrada,
    HorarioRespuesta,
    IglesiaPublica,
    SedeResumen,
)
from app.modulos.horarios.servicio import (
    actualizar_horario,
    crear_horario,
    eliminar_horario,
    iglesias_publicas,
    listar_horarios,
    listar_sedes,
)
from app.seguridad.permisos import requerir_cargos

router = APIRouter(tags=["horarios"])
Sesion = Annotated[Session, Depends(get_db)]
Editor = Annotated[Usuario, Depends(requerir_cargos("presbitero", "pastor", "apoyo_pastor"))]


@router.get("/publico/iglesias", response_model=list[IglesiaPublica])
def publico(sesion: Sesion):
    return iglesias_publicas(sesion)


@router.get("/sedes", response_model=list[SedeResumen])
def sedes(sesion: Sesion, actor: Editor):
    return listar_sedes(sesion, actor)


@router.get("/sedes/{sede_id}/horarios", response_model=list[HorarioRespuesta])
def listar(sede_id: int, sesion: Sesion, actor: Editor):
    return listar_horarios(sesion, actor, sede_id)


@router.post("/sedes/{sede_id}/horarios", response_model=HorarioRespuesta, status_code=201)
def crear(sede_id: int, datos: HorarioEntrada, sesion: Sesion, actor: Editor):
    return crear_horario(sesion, actor, sede_id, datos)


@router.put("/horarios/{identificador}", response_model=HorarioRespuesta)
def actualizar(identificador: int, datos: HorarioEntrada, sesion: Sesion, actor: Editor):
    return actualizar_horario(sesion, actor, identificador, datos)


@router.delete("/horarios/{identificador}", status_code=204)
def eliminar(identificador: int, sesion: Sesion, actor: Editor):
    eliminar_horario(sesion, actor, identificador)
    return Response(status_code=204)
