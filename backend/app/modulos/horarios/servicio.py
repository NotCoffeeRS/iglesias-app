"""Horarios con alcance por iglesia real y consulta pública explícita."""

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Horario, Iglesia, RedSocial, Sede, Usuario
from app.modulos.horarios.schemas import HorarioEntrada
from app.seguridad.permisos import validar_alcance


def listar_sedes(sesion: Session, actor: Usuario):
    consulta = (
        select(Sede.id, Sede.nombre, Iglesia.nombre.label("iglesia_nombre"))
        .join(Iglesia, Iglesia.id == Sede.iglesia_id)
        .order_by(Iglesia.nombre, Sede.nombre, Sede.id)
    )
    if actor.cargo != "presbitero":
        consulta = consulta.where(Sede.iglesia_id == actor.iglesia_id)
    return sesion.execute(consulta).mappings().all()


def obtener_sede(sesion: Session, actor: Usuario, identificador: int) -> Sede:
    sede = sesion.get(Sede, identificador)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada.")
    validar_alcance(sesion, actor, sede.iglesia_id)
    return sede


def listar_horarios(sesion: Session, actor: Usuario, sede_id: int):
    sede = obtener_sede(sesion, actor, sede_id)
    return list(
        sesion.scalars(
            select(Horario)
            .where(Horario.sede_id == sede.id)
            .order_by(Horario.dia, Horario.hora_inicio, Horario.id)
        )
    )


def guardar(sesion: Session):
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409,
            detail="El horario ya existe o sus datos relacionados cambiaron. Recarga la página.",
        ) from error


def crear_horario(sesion: Session, actor: Usuario, sede_id: int, datos: HorarioEntrada):
    sede = obtener_sede(sesion, actor, sede_id)
    horario = Horario(sede_id=sede.id, **datos.model_dump())
    sesion.add(horario)
    guardar(sesion)
    sesion.refresh(horario)
    return horario


def obtener_horario(sesion: Session, actor: Usuario, identificador: int) -> Horario:
    horario = sesion.get(Horario, identificador)
    if horario is None:
        raise HTTPException(status_code=404, detail="Horario no encontrado.")
    obtener_sede(sesion, actor, horario.sede_id)
    return horario


def actualizar_horario(
    sesion: Session,
    actor: Usuario,
    identificador: int,
    datos: HorarioEntrada,
):
    horario = obtener_horario(sesion, actor, identificador)
    for campo, valor in datos.model_dump().items():
        setattr(horario, campo, valor)
    guardar(sesion)
    sesion.refresh(horario)
    return horario


def eliminar_horario(sesion: Session, actor: Usuario, identificador: int):
    horario = obtener_horario(sesion, actor, identificador)
    sesion.delete(horario)
    guardar(sesion)


def iglesias_publicas(sesion: Session):
    # Cuatro consultas en total; solo se proyectan campos del contrato público.
    horarios = defaultdict(list)
    for horario in sesion.scalars(
        select(Horario).order_by(Horario.dia, Horario.hora_inicio, Horario.id)
    ):
        horarios[horario.sede_id].append(horario)
    sedes = defaultdict(list)
    for sede in sesion.scalars(select(Sede).order_by(Sede.nombre, Sede.id)):
        sedes[sede.iglesia_id].append(
            {
                "id": sede.id,
                "nombre": sede.nombre,
                "direccion": sede.direccion,
                "enlace_maps": sede.enlace_maps,
                "horarios": horarios[sede.id],
            }
        )
    redes = defaultdict(list)
    for red in sesion.scalars(select(RedSocial).order_by(RedSocial.id)):
        redes[red.iglesia_id].append(red)
    return [
        {
            "id": iglesia.id,
            "nombre": iglesia.nombre,
            "pastor": iglesia.pastor,
            "foto_url": iglesia.foto_url,
            "telefono_iglesia": iglesia.telefono_iglesia,
            "redes": redes[iglesia.id],
            "sedes": sedes[iglesia.id],
        }
        for iglesia in sesion.scalars(select(Iglesia).order_by(Iglesia.nombre, Iglesia.id))
    ]
