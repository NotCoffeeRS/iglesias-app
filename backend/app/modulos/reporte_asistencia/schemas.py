"""Totales de marcas guardadas, no de personas distintas ni días sin captura."""

from datetime import date

from pydantic import BaseModel


class Totales(BaseModel):
    registros: int
    asistencias: int
    faltas: int


class Detalle(Totales):
    fecha: date
    servicio: str


class IglesiaReporte(Totales):
    iglesia_id: int
    iglesia_nombre: str
    detalle: list[Detalle]


class Reporte(BaseModel):
    desde: date
    hasta: date
    servicio: str | None
    totales: Totales
    iglesias: list[IglesiaReporte]
