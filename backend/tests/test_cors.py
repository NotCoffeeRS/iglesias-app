"""CORS del #75: orígenes exactos, preflight JSON/Bearer y denegación del resto."""

import pytest
from fastapi.testclient import TestClient

from app.main import crear_app


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with TestClient(crear_app()) as cliente:
        yield cliente


@pytest.mark.parametrize("origen", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_origenes_locales_por_defecto(cliente, origen):
    respuesta = cliente.get("/salud", headers={"Origin": origen})
    assert respuesta.status_code == 200
    assert respuesta.headers["Access-Control-Allow-Origin"] == origen
    assert "Origin" in respuesta.headers["Vary"]
    assert "Access-Control-Allow-Credentials" not in respuesta.headers


@pytest.mark.parametrize(
    "origen",
    ["https://otra.example", "http://localhost:5174", "http://localhost:5173.otra.example"],
)
def test_otro_origen_no_recibe_cabeceras_cors(cliente, origen):
    respuesta = cliente.get("/salud", headers={"Origin": origen})
    assert respuesta.status_code == 200
    assert not any(nombre.startswith("access-control-") for nombre in respuesta.headers)


@pytest.mark.parametrize("metodo", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_preflight_admite_metodos_y_encabezados_del_cliente(cliente, metodo):
    respuesta = cliente.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": metodo,
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert metodo in respuesta.headers["Access-Control-Allow-Methods"]
    permitidos = respuesta.headers["Access-Control-Allow-Headers"].lower()
    assert "authorization" in permitidos
    assert "content-type" in permitidos
    assert "Access-Control-Allow-Credentials" not in respuesta.headers


def test_preflight_rechaza_origen_desconocido(cliente):
    respuesta = cliente.options(
        "/auth/login",
        headers={
            "Origin": "https://otra.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert respuesta.status_code == 400
    assert "Access-Control-Allow-Origin" not in respuesta.headers


def test_variable_de_entorno_admite_varios_origenes_y_reemplaza_los_locales(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS", " https://web.ficticia.example, , https://preview.ficticia.example "
    )
    with TestClient(crear_app()) as cliente:
        for origen in ["https://web.ficticia.example", "https://preview.ficticia.example"]:
            respuesta = cliente.get("/salud", headers={"Origin": origen})
            assert respuesta.headers["Access-Control-Allow-Origin"] == origen
        respuesta = cliente.get("/salud", headers={"Origin": "http://localhost:5173"})
        assert "Access-Control-Allow-Origin" not in respuesta.headers


def test_lista_vacia_no_habilita_origenes_por_defecto(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " , ")
    with TestClient(crear_app()) as cliente:
        respuesta = cliente.get("/salud", headers={"Origin": "http://localhost:5173"})
    assert "Access-Control-Allow-Origin" not in respuesta.headers


def test_peticion_sin_origin_conserva_respuesta(cliente):
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
    assert not any(nombre.startswith("access-control-") for nombre in respuesta.headers)


def test_error_de_validacion_tambien_tiene_cors(cliente):
    respuesta = cliente.post("/auth/login", headers={"Origin": "http://localhost:5173"}, json={})
    assert respuesta.status_code == 422
    assert respuesta.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


@pytest.mark.parametrize(
    "metodo,encabezados", [("TRACE", "authorization"), ("POST", "x-encabezado-no-permitido")]
)
def test_preflight_no_autoriza_metodos_o_encabezados_adicionales(cliente, metodo, encabezados):
    respuesta = cliente.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": metodo,
            "Access-Control-Request-Headers": encabezados,
        },
    )
    assert respuesta.status_code == 400
