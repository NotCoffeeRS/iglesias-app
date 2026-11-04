"""Hash, tokens y login JSON contra PostgreSQL temporal migrado con Alembic."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import jwt
import pytest
from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from alembic import command
from app.db import get_db
from app.main import crear_app
from app.modelos import Usuario
from app.modelos.utilidades import obtener_url_base_datos
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


@pytest.fixture(scope="module")
def motor_login():
    """Solo crea y borra su propia base temporal; nunca migra la base configurada."""
    url_texto = obtener_url_base_datos()
    if not url_texto or not url_texto.startswith("postgresql"):
        pytest.fail("Las pruebas de login requieren DATABASE_URL de PostgreSQL.", pytrace=False)
    url = make_url(url_texto)
    nombre = f"iglesias_login_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    creado = False
    try:
        try:
            with admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
            creado = True
        except DBAPIError:
            pass
        if not creado:
            pytest.fail(
                "No se pudo crear la base temporal del login; revisa PostgreSQL y CREATEDB.",
                pytrace=False,
            )
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.attributes["url"] = url.set(database=nombre)
        motor = create_engine(url.set(database=nombre))
        try:
            command.upgrade(config, "head")
            yield motor
        finally:
            motor.dispose()
    finally:
        if creado:
            with admin.connect() as conexion:
                conexion.execute(text(f'DROP DATABASE "{nombre}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def cuenta_login(motor_login):
    with motor_login.connect() as conexion:
        transaccion = conexion.begin()
        with Session(bind=conexion) as sesion:
            contrasena = secrets.token_urlsafe(24)
            usuario = Usuario(
                nombre_usuario="Cuenta.Ficticia",
                nombre_completo="Persona Ficticia",
                contrasena_hash=crear_hash(contrasena),
                cargo="presbitero",
                iglesia_id=None,
                activo=True,
            )
            sesion.add(usuario)
            sesion.flush()
            try:
                yield sesion, usuario, contrasena
            finally:
                if transaccion.is_active:
                    transaccion.rollback()


@pytest.fixture
def cliente_login(cuenta_login, clave):
    sesion, _, _ = cuenta_login
    aplicacion = crear_app()

    def sesion_prueba():
        yield sesion

    aplicacion.dependency_overrides[get_db] = sesion_prueba
    try:
        with TestClient(aplicacion) as cliente:
            yield cliente
    finally:
        aplicacion.dependency_overrides.clear()


def test_login_valido_devuelve_token_sin_exponer_credenciales(cliente_login, cuenta_login, caplog):
    _, usuario, contrasena = cuenta_login
    respuesta = cliente_login.post(
        "/auth/login", json={"usuario": usuario.nombre_usuario, "contrasena": contrasena}
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert set(datos) == {"access_token", "token_type"}
    assert datos["token_type"] == "bearer"
    assert validar_token(datos["access_token"]) == str(usuario.id)
    assert contrasena not in respuesta.text
    assert usuario.contrasena_hash not in respuesta.text
    assert contrasena not in caplog.text
    assert usuario.contrasena_hash not in caplog.text
    assert datos["access_token"] not in caplog.text


@pytest.mark.parametrize("nombre", ["cuenta.ficticia", "CUENTA.FICTICIA", "CuEnTa.FiCtIcIa"])
def test_login_no_distingue_mayusculas(cliente_login, cuenta_login, nombre):
    _, _, contrasena = cuenta_login
    respuesta = cliente_login.post(
        "/auth/login", json={"usuario": nombre, "contrasena": contrasena}
    )
    assert respuesta.status_code == 200


@pytest.mark.parametrize("caso", ["contrasena", "inexistente", "inactivo", "inyeccion_sql"])
def test_login_invalido_da_el_mismo_401(cliente_login, cuenta_login, caso, caplog):
    sesion, usuario, contrasena = cuenta_login
    nombre = usuario.nombre_usuario
    if caso == "contrasena":
        contrasena = "otra contraseña ficticia"
    elif caso == "inexistente":
        nombre = "cuenta.inexistente"
    elif caso == "inactivo":
        usuario.activo = False
        sesion.flush()
    else:
        nombre = "' OR 1=1 --"
    respuesta = cliente_login.post(
        "/auth/login", json={"usuario": nombre, "contrasena": contrasena}
    )
    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "Usuario o contraseña incorrectos."}
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"
    assert contrasena not in respuesta.text
    assert contrasena not in caplog.text
    assert usuario.contrasena_hash not in respuesta.text


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"usuario": ""},
        {"usuario": "x" * 61},
        {"usuario": {"dato": "valor"}},
        {},
    ],
)
def test_validacion_login_no_devuelve_el_cuerpo_con_contrasena(
    cliente_login, cuenta_login, cuerpo, caplog
):
    _, _, contrasena = cuenta_login
    respuesta = cliente_login.post("/auth/login", json={**cuerpo, "contrasena": contrasena})
    assert respuesta.status_code == 422
    assert contrasena not in respuesta.text
    assert contrasena not in caplog.text
    assert "input" not in respuesta.json()


def test_login_mantiene_documentacion_json(cliente_login):
    operacion = cliente_login.get("/openapi.json").json()["paths"]["/auth/login"]["post"]
    assert "application/json" in operacion["requestBody"]["content"]
    assert "application/json" in operacion["responses"]["200"]["content"]
