"""Contratos de horarios y proyección pública sin teléfonos personales."""

import re
from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modelos.listas import DIAS_SEMANA, TIPOS_SERVICIO


class HorarioEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    tipo: str
    dia: str
    hora_inicio: time
    hora_fin: time | None = None
    descripcion: str | None = Field(default=None, max_length=200)

    @field_validator("tipo")
    @classmethod
    def tipo_conocido(cls, valor: str) -> str:
        if valor not in TIPOS_SERVICIO:
            raise ValueError("Tipo de servicio no válido.")
        return valor

    @field_validator("dia")
    @classmethod
    def dia_conocido(cls, valor: str) -> str:
        if valor not in DIAS_SEMANA:
            raise ValueError("Día no válido.")
        return valor

    @field_validator("hora_inicio", "hora_fin", mode="before")
    @classmethod
    def hora_local(cls, valor):
        if valor is not None and (
            not isinstance(valor, str) or not re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", valor)
        ):
            raise ValueError("Indica una hora local HH:MM o HH:MM:SS.")
        return valor

    @model_validator(mode="after")
    def fin_posterior(self):
        if self.hora_fin is not None and self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora de fin debe ser posterior al inicio.")
        return self


class HorarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    dia: str
    hora_inicio: time
    hora_fin: time | None
    descripcion: str | None


class SedeResumen(BaseModel):
    id: int
    nombre: str
    iglesia_nombre: str


class RedPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nombre: str
    url: str


class SedePublica(BaseModel):
    id: int
    nombre: str
    direccion: str
    enlace_maps: str | None
    horarios: list[HorarioRespuesta]


class IglesiaPublica(BaseModel):
    id: int
    nombre: str
    pastor: str | None
    foto_url: str | None
    telefono_iglesia: str | None
    redes: list[RedPublica]
    sedes: list[SedePublica]
