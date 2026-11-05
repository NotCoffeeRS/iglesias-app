"""Contrato JSON confirmado con el frontend en el PR #38."""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class EntradaLogin(BaseModel):
    usuario: str = Field(min_length=1, max_length=60)
    contrasena: SecretStr = Field(min_length=1)


class RespuestaLogin(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
