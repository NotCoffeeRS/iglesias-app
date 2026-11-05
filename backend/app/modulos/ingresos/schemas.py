"""Contrato monetario decimal; no se reciben datos de donantes ni de auditoría."""

import re
from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.modelos.listas import TIPOS_INGRESO, TIPOS_SERVICIO


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Partida(Entrada):
    tipo: str
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    descripcion: str | None = None

    @field_validator("tipo")
    @classmethod
    def tipo_conocido(cls, valor: str) -> str:
        if valor not in TIPOS_INGRESO:
            raise ValueError("Tipo de ingreso no válido.")
        return valor

    @field_validator("monto", mode="before")
    @classmethod
    def monto_decimal(cls, valor):
        # Solo texto decimal, nunca flotantes binarios, exponentes ni redondeo implícito.
        if not isinstance(valor, str) or not re.fullmatch(r"[0-9]+(\.[0-9]{1,2})?", valor):
            raise ValueError("Escribe el monto como texto con hasta dos decimales.")
        return valor

    @model_validator(mode="after")
    def otras_con_descripcion(self):
        if self.tipo == "otras" and not self.descripcion:
            raise ValueError("Otras donaciones exige descripción.")
        return self


class IngresosNuevos(Entrada):
    iglesia_id: int = Field(gt=0)
    fecha: date
    culto: str | None = None
    partidas: list[Partida] = Field(min_length=1)

    @field_validator("culto")
    @classmethod
    def culto_conocido(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in TIPOS_SERVICIO:
            raise ValueError("Culto no válido.")
        return valor


class Anulacion(Entrada):
    motivo: str = Field(min_length=1)


class IngresoRespuesta(BaseModel):
    id: int
    iglesia_id: int
    iglesia_nombre: str
    fecha: date
    culto: str | None
    tipo: str
    monto: Decimal
    descripcion: str | None
    anulado: bool
    motivo_anulacion: str | None

    @field_serializer("monto")
    def monto_como_texto(self, valor: Decimal) -> str:
        return format(valor, ".2f")
