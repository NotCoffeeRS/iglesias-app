"""Sumas independientes evitan multiplicar ingresos por gastos al unir tablas."""

from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modelos import Gasto, Iglesia, Ingreso, Usuario
from app.modelos.listas import CATEGORIAS_GASTO, TIPOS_INGRESO
from app.seguridad.permisos import validar_alcance

CERO = Decimal("0.00")


def resumen(ingresos: dict, gastos: dict):
    total_ingresos = sum(ingresos.values(), CERO)
    total_gastos = sum(gastos.values(), CERO)
    return {
        "ingresos": total_ingresos,
        "gastos": total_gastos,
        "balance": total_ingresos - total_gastos,
        "ingresos_por_tipo": [{"clave": t, "monto": ingresos.get(t, CERO)} for t in TIPOS_INGRESO],
        "gastos_por_categoria": [
            {"clave": t, "monto": gastos.get(t, CERO)} for t in CATEGORIAS_GASTO
        ],
    }


def obtener_reporte(
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
    if iglesia_id is not None or actor.cargo != "presbitero":
        alcance = iglesia_id if iglesia_id is not None else actor.iglesia_id
        validar_alcance(sesion, actor, alcance, dinero=True)
    else:
        alcance = None
    consulta = select(Iglesia).order_by(Iglesia.nombre, Iglesia.id)
    if alcance is not None:
        consulta = consulta.where(Iglesia.id == alcance)
    iglesias = list(sesion.scalars(consulta))
    if iglesia_id is not None and not iglesias:
        raise HTTPException(status_code=404, detail="Iglesia no encontrada.")
    ids = [i.id for i in iglesias]
    ingresos = {i: {} for i in ids}
    gastos = {i: {} for i in ids}
    for modelo, campo, destino in (
        (Ingreso, Ingreso.tipo, ingresos),
        (Gasto, Gasto.categoria, gastos),
    ):
        sumas = sesion.execute(
            select(modelo.iglesia_id, campo, func.sum(modelo.monto))
            .where(
                modelo.iglesia_id.in_(ids),
                modelo.fecha >= desde,
                modelo.fecha <= hasta,
                modelo.anulado_en.is_(None),
            )
            .group_by(modelo.iglesia_id, campo)
        )
        for identificador, clave, monto in sumas:
            destino[identificador][clave] = monto
    consolidado = None
    if actor.cargo == "presbitero" and iglesia_id is None:
        consolidado = resumen(
            {t: sum((ingresos[i].get(t, CERO) for i in ids), CERO) for t in TIPOS_INGRESO},
            {t: sum((gastos[i].get(t, CERO) for i in ids), CERO) for t in CATEGORIAS_GASTO},
        )
    return {
        "desde": desde,
        "hasta": hasta,
        "consolidado": consolidado,
        "iglesias": [
            {
                "iglesia_id": i.id,
                "iglesia_nombre": i.nombre,
                **resumen(ingresos[i.id], gastos[i.id]),
            }
            for i in iglesias
        ],
    }
