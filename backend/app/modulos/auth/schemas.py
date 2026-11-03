"""Contrato JSON confirmado con el frontend en el PR #38."""

from typing import Literal

from pydantic import BaseModel, SecretStr


class EntradaLogin(BaseModel):
    usuario: str
    contrasena: SecretStr


class RespuestaLogin(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
