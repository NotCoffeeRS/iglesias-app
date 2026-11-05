"""Contrato del formulario de gastos, sin redondeo implícito de dinero."""

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.modelos.listas import CATEGORIAS_GASTO


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GastoNuevo(Entrada):
    iglesia_id: int = Field(gt=0)
    fecha: date
    categoria: str
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    nota: str | None = None

    @field_validator("categoria")
    @classmethod
    def categoria_conocida(cls, valor: str) -> str:
        if valor not in CATEGORIAS_GASTO:
            raise ValueError("Categoría de gasto no válida.")
        return valor

    @field_validator("monto", mode="before")
    @classmethod
    def monto_decimal(cls, valor):
        if not isinstance(valor, str) or not re.fullmatch(r"[0-9]+(\.[0-9]{1,2})?", valor):
            raise ValueError("Escribe el monto como texto con hasta dos decimales.")
        return valor


class Anulacion(Entrada):
    motivo: str = Field(min_length=1)


class GastoRespuesta(BaseModel):
    id: int
    iglesia_id: int
    iglesia_nombre: str
    fecha: date
    categoria: str
    monto: Decimal
    nota: str | None
    anulado: bool
    motivo_anulacion: str | None

    @field_serializer("monto")
    def monto_como_texto(self, valor: Decimal) -> str:
        return format(valor, ".2f")
