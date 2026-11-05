"""Contrato de iglesias compatible con el formulario web del #12."""

from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Nombre = Annotated[str, Field(min_length=1, max_length=150)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def limpiar_texto(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor


def enlace_web(valor: str | None) -> str | None:
    if valor is not None:
        try:
            enlace = urlsplit(valor)
            valido = enlace.scheme in {"http", "https"} and bool(enlace.hostname)
        except ValueError:
            valido = False
        if not valido:
            raise ValueError("Usa un enlace http o https válido.")
    return valor


class SedeEntrada(Entrada):
    id: int | None = Field(default=None, gt=0)
    nombre: Nombre
    direccion: str = Field(min_length=1)
    enlace_maps: str | None = None

    _enlace = field_validator("enlace_maps")(enlace_web)


class RedEntrada(Entrada):
    id: int | None = Field(default=None, gt=0)
    nombre: str = Field(min_length=1, max_length=60)
    url: str
    tipo: Literal["propia", "relacionada"]

    _enlace = field_validator("url")(enlace_web)


class IglesiaEntrada(Entrada):
    nombre: Nombre
    foto_url: str | None = None
    pastor: str | None = Field(default=None, max_length=150)
    telefono_pastor: str | None = Field(default=None, max_length=20)
    telefono_iglesia: str | None = Field(default=None, max_length=20)
    sedes: list[SedeEntrada] = Field(min_length=1)
    redes: list[RedEntrada]

    _enlace = field_validator("foto_url")(enlace_web)

    @model_validator(mode="after")
    def hijos_sin_duplicados(self):
        for elementos in (self.sedes, self.redes):
            ids = [e.id for e in elementos if e.id is not None]
            if len(ids) != len(set(ids)):
                raise ValueError("No repitas identificadores.")
        nombres = [s.nombre for s in self.sedes]
        if len(nombres) != len(set(nombres)):
            raise ValueError("Las sedes deben tener nombres distintos.")
        return self


class SedeRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    direccion: str
    enlace_maps: str | None


class RedRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    url: str
    tipo: Literal["propia", "relacionada"]


class IglesiaResumen(BaseModel):
    id: int
    nombre: str
    foto_url: str | None
    pastor: str | None
    total_sedes: int


class IglesiaRespuesta(BaseModel):
    id: int
    nombre: str
    foto_url: str | None
    pastor: str | None
    telefono_pastor: str | None
    telefono_iglesia: str | None
    sedes: list[SedeRespuesta]
    redes: list[RedRespuesta]
