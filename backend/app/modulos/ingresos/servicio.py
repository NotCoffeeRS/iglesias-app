"""Ingresos por partidas atómicas y anulación con auditoría del servidor."""

from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Iglesia, Ingreso, Usuario
from app.modulos.ingresos.schemas import IngresosNuevos
from app.seguridad.permisos import validar_alcance


def obtener_iglesia(sesion: Session, actor: Usuario, identificador: int) -> Iglesia:
    validar_alcance(sesion, actor, identificador, dinero=True)
    iglesia = sesion.get(Iglesia, identificador)
    if iglesia is None:
        raise HTTPException(status_code=404, detail="Iglesia no encontrada.")
    return iglesia


def respuesta(ingreso: Ingreso, nombre: str):
    return {
        "id": ingreso.id,
        "iglesia_id": ingreso.iglesia_id,
        "iglesia_nombre": nombre,
        "fecha": ingreso.fecha,
        "culto": ingreso.tipo_servicio,
        "tipo": ingreso.tipo,
        "monto": ingreso.monto,
        "descripcion": ingreso.descripcion,
        "anulado": ingreso.anulado_en is not None,
        "motivo_anulacion": ingreso.anulado_motivo,
    }


def listar_ingresos(
    sesion: Session,
    actor: Usuario,
    desde: date,
    hasta: date,
    iglesia_id: int | None,
):
    if desde > hasta:
        raise HTTPException(
            status_code=422, detail="La fecha inicial debe ser anterior o igual a la final."
        )
    if iglesia_id is not None:
        obtener_iglesia(sesion, actor, iglesia_id)
    elif actor.cargo != "presbitero":
        iglesia_id = actor.iglesia_id
        validar_alcance(sesion, actor, iglesia_id, dinero=True)
    consulta = (
        select(Ingreso, Iglesia.nombre)
        .join(Iglesia, Iglesia.id == Ingreso.iglesia_id)
        .where(Ingreso.fecha >= desde, Ingreso.fecha <= hasta)
        .order_by(Ingreso.fecha, Ingreso.id)
    )
    if iglesia_id is not None:
        consulta = consulta.where(Ingreso.iglesia_id == iglesia_id)
    return [respuesta(ingreso, nombre) for ingreso, nombre in sesion.execute(consulta)]


def guardar(sesion: Session):
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409,
            detail="Los datos relacionados cambiaron. Recarga antes de intentarlo de nuevo.",
        ) from error


def registrar_ingresos(sesion: Session, actor: Usuario, datos: IngresosNuevos):
    iglesia = obtener_iglesia(sesion, actor, datos.iglesia_id)
    ingresos = [
        Ingreso(
            iglesia_id=iglesia.id,
            fecha=datos.fecha,
            tipo_servicio=datos.culto,
            registrado_por=actor.id,
            **partida.model_dump(),
        )
        for partida in datos.partidas
    ]
    sesion.add_all(ingresos)
    guardar(sesion)
    return [respuesta(ingreso, iglesia.nombre) for ingreso in ingresos]


def anular_ingreso(sesion: Session, actor: Usuario, identificador: int, motivo: str):
    ingreso = sesion.scalar(select(Ingreso).where(Ingreso.id == identificador).with_for_update())
    if ingreso is None:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado.")
    iglesia = obtener_iglesia(sesion, actor, ingreso.iglesia_id)
    if ingreso.anulado_en is not None:
        raise HTTPException(status_code=409, detail="El ingreso ya está anulado.")
    ingreso.anulado_en = datetime.now(UTC)
    ingreso.anulado_motivo = motivo
    ingreso.anulado_por = actor.id
    guardar(sesion)
    return respuesta(ingreso, iglesia.nombre)
