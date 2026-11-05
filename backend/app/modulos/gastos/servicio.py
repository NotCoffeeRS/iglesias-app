"""Gastos con alcance financiero por iglesia y auditoría de anulación."""

from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modelos import Gasto, Iglesia, Usuario
from app.modulos.gastos.schemas import GastoNuevo
from app.seguridad.permisos import validar_alcance


def obtener_iglesia(sesion: Session, actor: Usuario, identificador: int) -> Iglesia:
    validar_alcance(sesion, actor, identificador, dinero=True)
    iglesia = sesion.get(Iglesia, identificador)
    if iglesia is None:
        raise HTTPException(status_code=404, detail="Iglesia no encontrada.")
    return iglesia


def respuesta(gasto: Gasto, nombre: str):
    return {
        "id": gasto.id,
        "iglesia_id": gasto.iglesia_id,
        "iglesia_nombre": nombre,
        "fecha": gasto.fecha,
        "categoria": gasto.categoria,
        "monto": gasto.monto,
        "nota": gasto.nota,
        "anulado": gasto.anulado_en is not None,
        "motivo_anulacion": gasto.anulado_motivo,
    }


def listar_gastos(
    sesion: Session,
    actor: Usuario,
    desde: date,
    hasta: date,
    iglesia_id: int | None,
):
    if desde > hasta:
        raise HTTPException(
            status_code=422,
            detail="La fecha inicial debe ser anterior o igual a la final.",
        )
    if iglesia_id is not None:
        obtener_iglesia(sesion, actor, iglesia_id)
    elif actor.cargo != "presbitero":
        iglesia_id = actor.iglesia_id
        validar_alcance(sesion, actor, iglesia_id, dinero=True)
    consulta = (
        select(Gasto, Iglesia.nombre)
        .join(Iglesia, Iglesia.id == Gasto.iglesia_id)
        .where(Gasto.fecha >= desde, Gasto.fecha <= hasta)
        .order_by(Gasto.fecha, Gasto.id)
    )
    if iglesia_id is not None:
        consulta = consulta.where(Gasto.iglesia_id == iglesia_id)
    return [respuesta(gasto, nombre) for gasto, nombre in sesion.execute(consulta)]


def guardar(sesion: Session):
    try:
        sesion.commit()
    except IntegrityError as error:
        sesion.rollback()
        raise HTTPException(
            status_code=409,
            detail="Los datos relacionados cambiaron. Recarga antes de intentarlo de nuevo.",
        ) from error


def registrar_gasto(sesion: Session, actor: Usuario, datos: GastoNuevo):
    iglesia = obtener_iglesia(sesion, actor, datos.iglesia_id)
    gasto = Gasto(registrado_por=actor.id, **datos.model_dump())
    sesion.add(gasto)
    guardar(sesion)
    return respuesta(gasto, iglesia.nombre)


def anular_gasto(sesion: Session, actor: Usuario, identificador: int, motivo: str):
    gasto = sesion.scalar(select(Gasto).where(Gasto.id == identificador).with_for_update())
    if gasto is None:
        raise HTTPException(status_code=404, detail="Gasto no encontrado.")
    iglesia = obtener_iglesia(sesion, actor, gasto.iglesia_id)
    if gasto.anulado_en is not None:
        raise HTTPException(status_code=409, detail="El gasto ya está anulado.")
    gasto.anulado_en = datetime.now(UTC)
    gasto.anulado_motivo = motivo
    gasto.anulado_por = actor.id
    guardar(sesion)
    return respuesta(gasto, iglesia.nombre)
