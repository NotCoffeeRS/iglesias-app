"""Contrato de miembros (#17), el mismo que usa la pantalla `frontend/src/api/miembros.ts`.

No hay campos de familia (D14): `extra="forbid"` rechaza cualquier campo que no esté aquí.
"""

import re
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modelos.listas import ESTADOS_CIVILES, ESTADOS_MIEMBRO

_CORREO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _texto_o_nulo(valor: str | None) -> str | None:
    """Los textos vacíos o solo con espacios se guardan como "sin dato"."""
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


class MiembroEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=150)
    telefono: str | None = Field(default=None, max_length=20)
    correo: str | None = Field(default=None, max_length=254)
    fecha_nacimiento: date | None = None
    direccion: str | None = None
    estado_civil: str | None = None
    fecha_bautizo: date | None = None
    fecha_ingreso: date | None = None
    iglesia_id: int = Field(gt=0)
    estado: str

    @field_validator("nombre")
    @classmethod
    def nombre_con_texto(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Escribe el nombre")
        return valor

    @field_validator("telefono", "direccion", mode="after")
    @classmethod
    def limpiar_texto(cls, valor: str | None) -> str | None:
        return _texto_o_nulo(valor)

    @field_validator("correo", mode="after")
    @classmethod
    def correo_valido(cls, valor: str | None) -> str | None:
        valor = _texto_o_nulo(valor)
        if valor is not None and not _CORREO.match(valor):
            raise ValueError("Correo no válido")
        return valor

    @field_validator("estado")
    @classmethod
    def estado_conocido(cls, valor: str) -> str:
        if valor not in ESTADOS_MIEMBRO:
            raise ValueError("Estado no válido")
        return valor

    @field_validator("estado_civil", mode="after")
    @classmethod
    def estado_civil_conocido(cls, valor: str | None) -> str | None:
        valor = _texto_o_nulo(valor)
        if valor is not None and valor not in ESTADOS_CIVILES:
            raise ValueError("Estado civil no válido")
        return valor


class MiembroRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    telefono: str | None
    correo: str | None
    fecha_nacimiento: date | None
    direccion: str | None
    estado_civil: str | None
    fecha_bautizo: date | None
    fecha_ingreso: date | None
    iglesia_id: int
    estado: str


class MiembroResumen(BaseModel):
    """Lo que necesita una lista: la ficha completa se pide aparte."""

    id: int
    nombre: str
    telefono: str | None
    estado: str
    iglesia_id: int
    iglesia_nombre: str


class Busqueda(BaseModel):
    """Búsqueda por nombre. Va en el cuerpo, no en la dirección, para no exponer nombres (§4.9)."""

    model_config = ConfigDict(extra="forbid")

    texto: str | None = Field(default=None, max_length=150)
    estado: str | None = None
    iglesia_id: int | None = Field(default=None, gt=0)

    @field_validator("estado")
    @classmethod
    def estado_conocido(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in ESTADOS_MIEMBRO:
            raise ValueError("Estado no válido")
        return valor
