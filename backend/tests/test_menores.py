"""HU-25: cumpleaños, tutores, privacidad y permisos confirmados del #19."""

from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Menor, Tutor
from app.modulos.menores import servicio


@pytest.fixture(autouse=True)
def fecha_fija(monkeypatch):
    monkeypatch.setattr(servicio, "hoy_en_merida", lambda: date(2026, 11, 5))


def entrada(iglesia_id, **cambios):
    return {
        "iglesia_id": iglesia_id,
        "nombre": "Menor de prueba",
        "fecha_nacimiento": "2016-11-05",
        "sexo": "femenino",
        "direccion": "Dirección ficticia",
        "activo": True,
        "tutores": [{"nombre": "Tutor ficticio", "telefono": "0000000000"}],
        **cambios,
    }


@pytest.fixture
def registro(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    menores = [
        Menor(
            iglesia_id=i.id,
            nombre=f"Menor ficticio {n}",
            fecha_nacimiento=date(2016, 11, 5),
            sexo="femenino",
            direccion="Dirección ficticia",
        )
        for n, i in enumerate(iglesias)
    ]
    sesion.add_all(menores)
    sesion.flush()
    sesion.add_all(
        [Tutor(menor_id=m.id, nombre="Tutor ficticio", telefono="0000000000") for m in menores]
    )
    sesion.commit()
    return cliente, sesion, cuentas, iglesias, menores


@pytest.mark.parametrize("sexo", ["femenino", "masculino"])
@pytest.mark.parametrize(
    "nacimiento,edad",
    [("2022-11-05", 4), ("2014-11-06", 11), ("2014-11-05", 12), ("2008-11-06", 17)],
)
def test_categoria_por_edad_cumplida_y_sexo(entorno, sexo, nacimiento, edad):
    cliente, _, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/menores",
        headers=autorizacion(cuentas, "pastor"),
        json=entrada(iglesias[0].id, sexo=sexo, fecha_nacimiento=nacimiento),
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["edad"] == edad
    esperado = "adolescente" if edad >= 12 else "nina" if sexo == "femenino" else "nino"
    assert respuesta.json()["categoria"] == esperado
    assert respuesta.json()["tutores"] == [{"nombre": "Tutor ficticio", "telefono": "0000000000"}]


@pytest.mark.parametrize(
    "nacimiento", ["2022-11-06", "2008-11-05", "2026-11-05", "2027-01-01", "2000-01-01"]
)
def test_rechaza_fuera_de_4_a_17_sin_crear_tutores(entorno, nacimiento):
    cliente, sesion, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/menores",
        headers=autorizacion(cuentas, "apoyo_pastor"),
        json=entrada(iglesias[0].id, fecha_nacimiento=nacimiento),
    )
    assert respuesta.status_code == 422
    assert sesion.scalar(select(func.count()).select_from(Menor)) == 0
    assert sesion.scalar(select(func.count()).select_from(Tutor)) == 0


@pytest.mark.parametrize(
    "cambios",
    [
        {"tutores": []},
        {"tutores": [{"nombre": "Ficticio"}]},
        {"tutores": [{"nombre": " ", "telefono": "0000"}]},
        {"tutores": [{"nombre": "Ficticio", "telefono": " "}]},
        {"tutores": [{"nombre": "Ficticio", "telefono": "0" * 21}]},
        {"sexo": "otro"},
        {"fecha_nacimiento": "2016-02-30"},
        {"direccion": " "},
        {"nombre": " "},
        {"categoria": "adolescente"},
        {"edad": 15},
    ],
)
def test_datos_obligatorios_y_no_se_captura_categoria(entorno, cambios):
    cliente, _, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/menores", headers=autorizacion(cuentas, "pastor"), json=entrada(iglesias[0].id, **cambios)
    )
    assert respuesta.status_code == 422
    assert "input" not in respuesta.text
    assert "Menor de prueba" not in respuesta.text
    assert "Dirección ficticia" not in respuesta.text


@pytest.mark.parametrize("cargo", CARGOS)
def test_solo_tres_cargos_consultan_y_gestionan(registro, cargo):
    cliente, _, cuentas, iglesias, menores = registro
    headers = autorizacion(cuentas, cargo)
    permitido = cargo in {"presbitero", "pastor", "apoyo_pastor"}
    assert cliente.get("/menores", headers=headers).status_code == (200 if permitido else 403)
    assert cliente.get(f"/menores/{menores[0].id}", headers=headers).status_code == (
        200 if permitido else 403
    )
    assert cliente.post("/menores", headers=headers, json=entrada(iglesias[0].id)).status_code == (
        201 if permitido else 403
    )
    assert cliente.put(
        f"/menores/{menores[0].id}", headers=headers, json=entrada(iglesias[0].id)
    ).status_code == (200 if permitido else 403)


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor", "presbitero"])
def test_alcance_por_iglesia_real_y_listado_sin_direccion_ni_tutores(registro, cargo):
    cliente, _, cuentas, iglesias, menores = registro
    headers = autorizacion(cuentas, cargo)
    listado = cliente.get("/menores", headers=headers).json()
    assert {m["iglesia_id"] for m in listado} == {
        i.id for i in iglesias if cargo == "presbitero" or i.id == iglesias[0].id
    }
    assert "direccion" not in listado[0]
    assert "tutores" not in listado[0]
    esperado = 200 if cargo == "presbitero" else 404
    assert cliente.get(f"/menores/{menores[1].id}", headers=headers).status_code == esperado
    assert (
        cliente.put(
            f"/menores/{menores[1].id}", headers=headers, json=entrada(iglesias[1].id)
        ).status_code
        == esperado
    )
    assert cliente.post("/menores", headers=headers, json=entrada(iglesias[1].id)).status_code == (
        201 if esperado == 200 else 403
    )
    assert cliente.get(f"/menores?iglesia_id={iglesias[1].id}", headers=headers).status_code == (
        200 if esperado == 200 else 403
    )
    assert cliente.put(
        f"/menores/{menores[0].id}", headers=headers, json=entrada(iglesias[1].id)
    ).status_code == (200 if esperado == 200 else 403)


def test_edicion_guarda_varios_tutores_y_recalcula_categoria(registro):
    cliente, sesion, cuentas, iglesias, menores = registro
    datos = entrada(
        iglesias[0].id,
        fecha_nacimiento="2014-11-05",
        sexo="masculino",
        tutores=[
            {"nombre": "Tutor ficticio A", "telefono": "0000000001"},
            {"nombre": "Tutor ficticio B", "telefono": "0000000002"},
        ],
    )
    headers = autorizacion(cuentas, "apoyo_pastor")
    url = f"/menores/{menores[0].id}"
    respuesta = cliente.put(url, headers=headers, json=datos)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["categoria"] == "adolescente"
    assert respuesta.json()["edad"] == 12
    assert respuesta.json()["tutores"] == datos["tutores"]
    assert (
        sesion.scalar(
            select(func.count()).select_from(Tutor).where(Tutor.menor_id == menores[0].id)
        )
        == 2
    )
    assert cliente.get(url, headers=headers).json() == respuesta.json()
    assert cliente.delete(url, headers=headers).status_code == 405


@pytest.mark.parametrize("operacion", ["alta", "edicion"])
def test_fallo_no_deja_menor_sin_tutores_ni_cambios_parciales(registro, monkeypatch, operacion):
    cliente, sesion, cuentas, iglesias, menores = registro
    headers = autorizacion(cuentas, "presbitero")
    url = f"/menores/{menores[0].id}"
    anterior = cliente.get(url, headers=headers).json()

    def fallo_al_confirmar():
        sesion.flush()
        raise IntegrityError("fallo simulado", {}, Exception("prueba"))

    monkeypatch.setattr(sesion, "commit", fallo_al_confirmar)
    if operacion == "alta":
        respuesta = cliente.post("/menores", headers=headers, json=entrada(iglesias[0].id))
    else:
        respuesta = cliente.put(
            url, headers=headers, json=entrada(iglesias[0].id, nombre="Cambio descartado")
        )
    assert respuesta.status_code == 409
    assert sesion.scalar(select(func.count()).select_from(Menor)) == 2
    assert sesion.scalar(select(func.count()).select_from(Tutor)) == 2
    assert cliente.get(url, headers=headers).json() == anterior


def test_sesion_obligatoria_privacidad_y_recursos_inexistentes(registro):
    cliente, _, cuentas, iglesias, menores = registro
    assert cliente.get("/menores").status_code == 401
    assert cliente.get(f"/menores/{menores[0].id}").status_code == 401
    assert cliente.post("/menores", json=entrada(iglesias[0].id)).status_code == 401
    assert cliente.put(f"/menores/{menores[0].id}", json=entrada(iglesias[0].id)).status_code == 401
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.get("/menores/2147483647", headers=headers).status_code == 404
    assert cliente.post("/menores", headers=headers, json=entrada(2147483647)).status_code == 422
    publico = cliente.get("/publico/iglesias").text
    assert "Tutor ficticio" not in publico
    assert "Menor ficticio" not in publico
    assert "0000000000" not in publico


def test_categoria_se_actualiza_en_consulta_al_cumplir_anos(registro, monkeypatch):
    cliente, _, cuentas, _, menores = registro
    monkeypatch.setattr(servicio, "hoy_en_merida", lambda: date(2028, 11, 5))
    respuesta = cliente.get(f"/menores/{menores[0].id}", headers=autorizacion(cuentas, "pastor"))
    assert respuesta.json()["edad"] == 12
    assert respuesta.json()["categoria"] == "adolescente"
    # Al pasar de 17 se conserva el registro histórico sin inventar otra categoría.
    monkeypatch.setattr(servicio, "hoy_en_merida", lambda: date(2034, 11, 5))
    respuesta = cliente.get(f"/menores/{menores[0].id}", headers=autorizacion(cuentas, "pastor"))
    assert respuesta.json()["edad"] == 18
    assert respuesta.json()["categoria"] is None


def test_edad_cumplida_ano_bisiesto():
    assert servicio.edad_cumplida(date(2012, 2, 29), date(2026, 2, 28)) == 13
    assert servicio.edad_cumplida(date(2012, 2, 29), date(2026, 3, 1)) == 14
