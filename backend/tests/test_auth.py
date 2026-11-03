"""Seguridad del #7; la integración de login espera los modelos del #4."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.modulos.auth.schemas import EntradaLogin, RespuestaLogin
from app.seguridad.contrasenas import crear_hash, verificar_contrasena
from app.seguridad.tokens import crear_token, obtener_usuario_id, validar_token


@pytest.fixture
def clave(monkeypatch):
    valor = secrets.token_urlsafe(32)
    monkeypatch.setenv("SECRET_KEY", valor)
    return valor


@pytest.fixture
def cliente(clave):
    # Ruta exclusiva de pruebas: no introduce una API de usuarios ficticia en producción.
    aplicacion = FastAPI()

    @aplicacion.get("/protegido-prueba")
    def protegido(usuario_id: Annotated[str, Depends(obtener_usuario_id)]):
        return {"usuario_id": usuario_id}

    with TestClient(aplicacion) as cliente:
        yield cliente


def test_contrasenas_con_hash_sal_y_verificacion(caplog):
    contrasena = secrets.token_urlsafe(24)
    hash_a = crear_hash(contrasena)
    hash_b = crear_hash(contrasena)
    assert hash_a.startswith("$argon2id$")
    assert hash_a != hash_b
    assert contrasena not in hash_a
    assert verificar_contrasena(contrasena, hash_a)
    assert not verificar_contrasena("otra contraseña ficticia", hash_a)
    assert contrasena not in caplog.text
    assert hash_a not in caplog.text


@pytest.mark.parametrize("hash_invalido", ["", "texto plano", "$argon2id$invalido"])
def test_hash_invalido_no_autentica(hash_invalido):
    assert not verificar_contrasena("contraseña ficticia", hash_invalido)


def test_token_valido_y_expiracion(clave):
    token = crear_token("17")
    assert validar_token(token) == "17"
    contenido = jwt.decode(token, clave, algorithms=["HS256"])
    assert set(contenido) == {"sub", "iat", "exp"}
    assert contenido["exp"] - contenido["iat"] == 30 * 60


def test_ruta_protegida_acepta_token_valido(cliente):
    respuesta = cliente.get(
        "/protegido-prueba", headers={"Authorization": f"Bearer {crear_token('17')}"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"usuario_id": "17"}


@pytest.mark.parametrize("modo", ["vencido", "alterado", "otra_clave", "sin_exp", "algoritmo"])
def test_ruta_rechaza_tokens_invalidos_con_401(cliente, clave, modo):
    ahora = datetime.now(UTC)
    contenido = {"sub": "17", "iat": ahora, "exp": ahora + timedelta(minutes=30)}
    algoritmo = "HS256"
    firma = clave
    if modo == "vencido":
        contenido["iat"] = ahora - timedelta(hours=1)
        contenido["exp"] = ahora - timedelta(minutes=30)
    elif modo == "otra_clave":
        firma = secrets.token_urlsafe(32)
    elif modo == "sin_exp":
        contenido.pop("exp")
    elif modo == "algoritmo":
        algoritmo = "HS384"
        firma = secrets.token_urlsafe(48)
    token = jwt.encode(contenido, firma, algorithm=algoritmo)
    if modo == "alterado":
        cabecera, datos, firma_token = token.split(".")
        firma_token = ("A" if firma_token[0] != "A" else "B") + firma_token[1:]
        token = f"{cabecera}.{datos}.{firma_token}"
    respuesta = cliente.get("/protegido-prueba", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "Sesión no válida o vencida"}
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"
    assert token not in respuesta.text


@pytest.mark.parametrize("cabecera", [None, "Basic inventado", "Bearer invalido"])
def test_ruta_rechaza_sesion_ausente_o_malformada(cliente, cabecera):
    respuesta = cliente.get(
        "/protegido-prueba", headers={"Authorization": cabecera} if cabecera else {}
    )
    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("valor", [None, "", "demasiado-corta"])
def test_no_se_emiten_tokens_sin_secreto_valido(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("SECRET_KEY", valor)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        crear_token("17")


def test_token_sujeto_vacio_no_es_valido(clave):
    ahora = datetime.now(UTC)
    token = jwt.encode(
        {"sub": " ", "iat": ahora, "exp": ahora + timedelta(minutes=30)}, clave, algorithm="HS256"
    )
    with pytest.raises(HTTPException) as error:
        validar_token(token)
    assert error.value.status_code == 401


def test_contrato_login_oculta_contrasena_en_repr():
    contrasena = secrets.token_urlsafe(24)
    entrada = EntradaLogin(usuario="usuario_ficticio", contrasena=contrasena)
    assert entrada.contrasena.get_secret_value() == contrasena
    assert contrasena not in repr(entrada)
    salida = RespuestaLogin(access_token="token_ficticio")
    assert salida.model_dump() == {"access_token": "token_ficticio", "token_type": "bearer"}
