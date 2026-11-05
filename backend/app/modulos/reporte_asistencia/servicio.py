"""Alcance confirmado: iglesia, grupos dirigidos o sin célula según el cargo."""

from datetime import date

from fastapi import HTTPException
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session

from app.modelos import Asistencia, Grupo, GrupoMiembro, Iglesia, Miembro, Usuario
from app.modelos.listas import TIPOS_SERVICIO_ASISTENCIA
from app.seguridad.permisos import denegar


def totales(filas):
    presentes = sum(f["asistencias"] for f in filas)
    faltas = sum(f["faltas"] for f in filas)
    return {"registros": presentes + faltas, "asistencias": presentes, "faltas": faltas}


def obtener_reporte(
    sesion: Session,
    actor: Usuario,
    desde: date,
    hasta: date,
    iglesia_id: int | None,
    servicio: str | None,
):
    if actor.cargo == "tesorero":
        denegar()
    if desde > hasta:
        raise HTTPException(422, "La fecha inicial debe ser anterior o igual a la final.")
    if servicio is not None and servicio not in TIPOS_SERVICIO_ASISTENCIA:
        raise HTTPException(422, "Servicio no válido.")
    if actor.cargo != "presbitero":
        if actor.iglesia_id is None or (iglesia_id is not None and iglesia_id != actor.iglesia_id):
            denegar()
        iglesia_id = actor.iglesia_id
    consulta = select(Iglesia).order_by(Iglesia.nombre, Iglesia.id)
    if iglesia_id is not None:
        consulta = consulta.where(Iglesia.id == iglesia_id)
    iglesias = list(sesion.scalars(consulta))
    if iglesia_id is not None and not iglesias:
        raise HTTPException(404, "Iglesia no encontrada.")
    ids = [i.id for i in iglesias]
    miembros = select(Miembro.id).where(Miembro.iglesia_id.in_(ids))
    if actor.cargo == "ujier":
        con_celula = select(GrupoMiembro.miembro_id).where(GrupoMiembro.tipo_grupo == "celula")
        miembros = miembros.where(Miembro.estado != "inactivo", Miembro.id.not_in(con_celula))
    elif actor.cargo not in {"presbitero", "pastor", "apoyo_pastor"}:
        if actor.miembro_id is None:
            miembros = miembros.where(false())
        else:
            dirigidos = select(Grupo.id).where(
                Grupo.activo.is_(True),
                Grupo.lider_miembro_id == actor.miembro_id,
                Grupo.iglesia_id == actor.iglesia_id,
            )
            integrantes = select(GrupoMiembro.miembro_id).where(
                GrupoMiembro.grupo_id.in_(dirigidos)
            )
            miembros = miembros.where(Miembro.id.in_(integrantes))
    marcas = (
        select(
            Miembro.iglesia_id,
            Asistencia.fecha,
            Asistencia.tipo_servicio,
            func.count().filter(Asistencia.presente.is_(True)).label("asistencias"),
            func.count().filter(Asistencia.presente.is_(False)).label("faltas"),
        )
        .join(Miembro, Miembro.id == Asistencia.miembro_id)
        .where(
            Asistencia.miembro_id.in_(miembros),
            Asistencia.fecha >= desde,
            Asistencia.fecha <= hasta,
        )
        .group_by(Miembro.iglesia_id, Asistencia.fecha, Asistencia.tipo_servicio)
        .order_by(Asistencia.fecha, Asistencia.tipo_servicio)
    )
    if servicio is not None:
        marcas = marcas.where(Asistencia.tipo_servicio == servicio)
    detalles = {i: [] for i in ids}
    for fila in sesion.execute(marcas).mappings():
        detalles[fila["iglesia_id"]].append(
            {
                "fecha": fila["fecha"],
                "servicio": fila["tipo_servicio"],
                "asistencias": fila["asistencias"],
                "faltas": fila["faltas"],
                "registros": fila["asistencias"] + fila["faltas"],
            }
        )
    filas = [
        {
            "iglesia_id": i.id,
            "iglesia_nombre": i.nombre,
            **totales(detalles[i.id]),
            "detalle": detalles[i.id],
        }
        for i in iglesias
    ]
    return {
        "desde": desde,
        "hasta": hasta,
        "servicio": servicio,
        "totales": totales(filas),
        "iglesias": filas,
    }
