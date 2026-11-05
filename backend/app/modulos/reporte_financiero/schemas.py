"""Contrato de la pantalla del #30: dinero como texto con dos decimales."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class Partida(BaseModel):
    clave: str
    monto: Decimal

    @field_serializer("monto")
    def dinero(self, valor: Decimal) -> str:
        return format(valor, ".2f")


class Resumen(BaseModel):
    ingresos: Decimal
    gastos: Decimal
    balance: Decimal
    ingresos_por_tipo: list[Partida]
    gastos_por_categoria: list[Partida]

    @field_serializer("ingresos", "gastos", "balance")
    def dinero(self, valor: Decimal) -> str:
        return format(valor, ".2f")


class ResumenIglesia(Resumen):
    iglesia_id: int
    iglesia_nombre: str


class Reporte(BaseModel):
    desde: date
    hasta: date
    iglesias: list[ResumenIglesia]
    consolidado: Resumen | None
