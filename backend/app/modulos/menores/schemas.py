"""Datos de menores y tutores; edad y categoría solo son de salida."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TutorEntrada(Entrada):
    nombre: str = Field(min_length=1, max_length=150)
    telefono: str = Field(min_length=1, max_length=20)


class MenorEntrada(Entrada):
    iglesia_id: int = Field(gt=0)
    nombre: str = Field(min_length=1, max_length=150)
    fecha_nacimiento: date
    sexo: Literal["femenino", "masculino"]
    direccion: str = Field(min_length=1)
    activo: bool = True
    tutores: list[TutorEntrada] = Field(min_length=1)


class TutorRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nombre: str
    telefono: str


class MenorResumen(BaseModel):
    id: int
    iglesia_id: int
    iglesia_nombre: str
    nombre: str
    fecha_nacimiento: date
    sexo: Literal["femenino", "masculino"]
    edad: int
    categoria: Literal["nino", "nina", "adolescente"] | None
    activo: bool


class MenorRespuesta(MenorResumen):
    direccion: str | None
    tutores: list[TutorRespuesta]
