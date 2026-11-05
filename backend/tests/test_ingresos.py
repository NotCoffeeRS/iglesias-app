"""HU-15: dinero decimal, partidas atómicas, auditoría y permisos con PostgreSQL."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Ingreso
from app.modelos.listas import TIPOS_INGRESO, TIPOS_SERVICIO

FILTRO = "?desde=2026-11-01&hasta=2026-11-30"


def partida(**cambios):
    return {"tipo": "diezmos", "monto": "100.50", "descripcion": None, **cambios}


def entrada(iglesia_id, **cambios):
    return {
        "iglesia_id": iglesia_id,
        "fecha": "2026-11-05",
        "culto": "culto_domingo",
        "partidas": [partida()],
        **cambios,
    }


@pytest.fixture
def caja(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    ingresos = [
        Ingreso(
            iglesia_id=i.id,
            fecha=date(2026, 11, 5),
            tipo="ofrendas",
            monto=Decimal("25.00"),
            registrado_por=cuentas["presbitero"].id,
        )
        for i in iglesias
    ]
    sesion.add_all(ingresos)
    sesion.commit()
    return cliente, sesion, cuentas, iglesias, ingresos


@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "presbitero"])
def test_registro_partidas_decimales_contrato_y_auditoria(entorno, cargo):
    cliente, sesion, cuentas, iglesias, _ = entorno
    partes = [
        partida(tipo=t, monto="0.10", descripcion="Donación ficticia" if t == "otras" else None)
        for t in TIPOS_INGRESO
    ]
    resultado = cliente.post(
        "/ingresos",
        headers=autorizacion(cuentas, cargo),
        json=entrada(iglesias[0].id, partidas=partes),
    )
    assert resultado.status_code == 201, resultado.text
    datos = resultado.json()
    assert len(datos) == 5
    assert sum(Decimal(i["monto"]) for i in datos) == Decimal("0.50")
    for ingreso in datos:
        assert set(ingreso) == {
            "id",
            "iglesia_id",
            "iglesia_nombre",
            "fecha",
            "culto",
            "tipo",
            "monto",
            "descripcion",
            "anulado",
            "motivo_anulacion",
        }
        assert ingreso["monto"] == "0.10"
        assert ingreso["anulado"] is False
        assert ingreso["motivo_anulacion"] is None
        assert ingreso["iglesia_nombre"] == iglesias[0].nombre
        guardado = sesion.get(Ingreso, ingreso["id"])
        assert guardado.registrado_por == cuentas[cargo].id
        assert guardado.monto == Decimal("0.10")
        assert guardado.tipo_servicio == "culto_domingo"


@pytest.mark.parametrize(
    "monto,esperado",
    [
        ("0.01", "0.01"),
        ("1500", "1500.00"),
        ("1500.5", "1500.50"),
        ("9999999999.99", "9999999999.99"),
    ],
)
def test_limites_y_formato_dinero_sin_redondeo(entorno, monto, esperado):
    cliente, _, cuentas, iglesias, _ = entorno
    resultado = cliente.post(
        "/ingresos",
        headers=autorizacion(cuentas, "tesorero"),
        json=entrada(iglesias[0].id, partidas=[partida(monto=monto)]),
    )
    assert resultado.status_code == 201, resultado.text
    assert resultado.json()[0]["monto"] == esperado


@pytest.mark.parametrize(
    "monto",
    [
        "0",
        "0.00",
        "-1.00",
        "1.001",
        "0.009",
        "10000000000.00",
        "NaN",
        "Infinity",
        "1e2",
        "1,50",
        "",
        10.5,
        10,
        None,
        True,
    ],
)
def test_monto_invalido_rechaza_todo_el_lote(entorno, monto):
    cliente, sesion, cuentas, iglesias, _ = entorno
    datos = entrada(iglesias[0].id, partidas=[partida(), partida(monto=monto)])
    resultado = cliente.post("/ingresos", headers=autorizacion(cuentas, "tesorero"), json=datos)
    assert resultado.status_code == 422
    assert sesion.scalar(select(func.count()).select_from(Ingreso)) == 0
    assert "input" not in resultado.text


@pytest.mark.parametrize(
    "cambios",
    [
        {"tipo": "otro"},
        {"tipo": "otras", "descripcion": None},
        {"tipo": "otras", "descripcion": "  "},
        {"persona_id": 1},
        {"miembro_id": 1},
        {"donante": "Dato ficticio que no se registra"},
    ],
)
def test_no_donantes_tipo_cerrado_y_otras_exige_descripcion(entorno, cambios):
    cliente, sesion, cuentas, iglesias, _ = entorno
    resultado = cliente.post(
        "/ingresos",
        headers=autorizacion(cuentas, "pastor"),
        json=entrada(iglesias[0].id, partidas=[partida(**cambios)]),
    )
    assert resultado.status_code == 422
    assert sesion.scalar(select(func.count()).select_from(Ingreso)) == 0
    assert "Dato ficticio que no se registra" not in resultado.text


@pytest.mark.parametrize("culto", [None, *TIPOS_SERVICIO])
def test_culto_opcional_y_lista_de_la_base(entorno, culto):
    cliente, _, cuentas, iglesias, _ = entorno
    resultado = cliente.post(
        "/ingresos",
        headers=autorizacion(cuentas, "pastor"),
        json=entrada(iglesias[0].id, culto=culto),
    )
    assert resultado.status_code == 201
    assert resultado.json()[0]["culto"] == culto


@pytest.mark.parametrize(
    "cambios",
    [
        {"partidas": []},
        {"culto": "otro"},
        {"fecha": "2026-02-30"},
        {"registrado_por": 1},
        {"anulado": True},
        {"persona_id": 1},
    ],
)
def test_cuerpo_no_puede_falsificar_auditoria_ni_estado(entorno, cambios):
    cliente, _, cuentas, iglesias, _ = entorno
    resultado = cliente.post(
        "/ingresos",
        headers=autorizacion(cuentas, "presbitero"),
        json=entrada(iglesias[0].id, **cambios),
    )
    assert resultado.status_code == 422


@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "presbitero"])
def test_anular_conserva_ingreso_monto_y_auditoria(caja, cargo):
    cliente, sesion, cuentas, _, ingresos = caja
    ingreso = ingresos[0]
    headers = autorizacion(cuentas, cargo)
    url = f"/ingresos/{ingreso.id}/anular"
    respuesta = cliente.post(
        url, headers=headers, json={"motivo": "  Captura ficticia duplicada  "}
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["anulado"] is True
    assert respuesta.json()["motivo_anulacion"] == "Captura ficticia duplicada"
    assert respuesta.json()["monto"] == "25.00"
    guardado = sesion.get(Ingreso, ingreso.id)
    assert guardado.anulado_por == cuentas[cargo].id
    assert guardado.anulado_en is not None
    assert guardado.registrado_por == cuentas["presbitero"].id
    instante = guardado.anulado_en
    assert cliente.post(url, headers=headers, json={"motivo": "Otro motivo"}).status_code == 409
    assert sesion.get(Ingreso, ingreso.id).anulado_en == instante
    assert guardado.anulado_motivo == "Captura ficticia duplicada"
    listado = cliente.get("/ingresos" + FILTRO, headers=headers).json()
    assert next(i for i in listado if i["id"] == ingreso.id)["anulado"] is True
    assert cliente.delete(f"/ingresos/{ingreso.id}", headers=headers).status_code in {404, 405}
    assert sesion.get(Ingreso, ingreso.id) is not None


@pytest.mark.parametrize(
    "datos", [{}, {"motivo": ""}, {"motivo": "   "}, {"motivo": "Ficticio", "anulado_por": 1}]
)
def test_anulacion_exige_motivo_y_no_admite_auditoria_cliente(caja, datos):
    cliente, sesion, cuentas, _, ingresos = caja
    respuesta = cliente.post(
        f"/ingresos/{ingresos[0].id}/anular", headers=autorizacion(cuentas, "tesorero"), json=datos
    )
    assert respuesta.status_code == 422
    assert sesion.get(Ingreso, ingresos[0].id).anulado_en is None


@pytest.mark.parametrize(
    "cargo", [c for c in CARGOS if c not in {"pastor", "tesorero", "presbitero"}]
)
def test_sin_acceso_a_dinero_403_en_todas_las_operaciones(caja, cargo):
    cliente, _, cuentas, iglesias, ingresos = caja
    headers = autorizacion(cuentas, cargo)
    assert cliente.get("/ingresos" + FILTRO, headers=headers).status_code == 403
    assert (
        cliente.post("/ingresos", headers=headers, json=entrada(iglesias[0].id)).status_code == 403
    )
    assert (
        cliente.post(
            f"/ingresos/{ingresos[0].id}/anular",
            headers=headers,
            json={"motivo": "Motivo ficticio"},
        ).status_code
        == 403
    )


@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "presbitero"])
def test_alcance_por_iglesia_en_listado_registro_y_anulacion(caja, cargo):
    cliente, _, cuentas, iglesias, ingresos = caja
    headers = autorizacion(cuentas, cargo)
    listado = cliente.get("/ingresos" + FILTRO, headers=headers)
    assert listado.status_code == 200
    assert {i["iglesia_id"] for i in listado.json()} == {
        i.id for i in iglesias if cargo == "presbitero" or i.id == iglesias[0].id
    }
    estado = 200 if cargo == "presbitero" else 403
    assert (
        cliente.get(
            "/ingresos" + FILTRO + f"&iglesia_id={iglesias[1].id}", headers=headers
        ).status_code
        == estado
    )
    assert cliente.post("/ingresos", headers=headers, json=entrada(iglesias[1].id)).status_code == (
        201 if estado == 200 else 403
    )
    assert (
        cliente.post(
            f"/ingresos/{ingresos[1].id}/anular?iglesia_id={iglesias[0].id}",
            headers=headers,
            json={"motivo": "Motivo ficticio"},
        ).status_code
        == estado
    )


def test_filtros_fechas_inclusivas_y_vacios(caja):
    cliente, _, cuentas, iglesias, _ = caja
    headers = autorizacion(cuentas, "presbitero")
    url = f"/ingresos?desde=2026-11-05&hasta=2026-11-05&iglesia_id={iglesias[0].id}"
    assert len(cliente.get(url, headers=headers).json()) == 1
    assert cliente.get("/ingresos?desde=2026-11-06&hasta=2026-11-30", headers=headers).json() == []
    assert (
        cliente.get("/ingresos?desde=2026-11-30&hasta=2026-11-01", headers=headers).status_code
        == 422
    )
    assert (
        cliente.get("/ingresos?desde=no-fecha&hasta=2026-11-30", headers=headers).status_code == 422
    )
    assert cliente.get("/ingresos", headers=headers).status_code == 422
    assert cliente.get("/ingresos" + FILTRO + "&iglesia_id=0", headers=headers).status_code == 422


def test_error_despues_de_insertar_revierte_todo_el_lote(entorno, monkeypatch):
    cliente, sesion, cuentas, iglesias, _ = entorno

    def fallo_al_confirmar():
        sesion.flush()
        # Simula un fallo de integridad al confirmar, tras enviar las partidas a PostgreSQL.
        raise IntegrityError("fallo simulado de prueba", {}, Exception("prueba"))

    monkeypatch.setattr(sesion, "commit", fallo_al_confirmar)
    respuesta = cliente.post(
        "/ingresos",
        headers=autorizacion(cuentas, "tesorero"),
        json=entrada(iglesias[0].id, partidas=[partida(), partida(tipo="ofrendas")]),
    )
    assert respuesta.status_code == 409
    assert sesion.scalar(select(func.count()).select_from(Ingreso)) == 0


def test_sesion_requerida_y_404_sin_recursos(caja):
    cliente, _, cuentas, iglesias, ingresos = caja
    assert cliente.get("/ingresos" + FILTRO).status_code == 401
    assert cliente.post("/ingresos", json=entrada(iglesias[0].id)).status_code == 401
    assert (
        cliente.post(f"/ingresos/{ingresos[0].id}/anular", json={"motivo": "Ficticio"}).status_code
        == 401
    )
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.post("/ingresos", headers=headers, json=entrada(2147483647)).status_code == 404
    assert (
        cliente.get("/ingresos" + FILTRO + "&iglesia_id=2147483647", headers=headers).status_code
        == 404
    )
    assert (
        cliente.post(
            "/ingresos/2147483647/anular", headers=headers, json={"motivo": "Ficticio"}
        ).status_code
        == 404
    )


def test_revocacion_de_cargo_y_cuenta_inactiva_se_aplican_al_token(caja):
    cliente, sesion, cuentas, iglesias, _ = caja
    headers = autorizacion(cuentas, "tesorero")
    cuentas["tesorero"].cargo = "apoyo_pastor"
    sesion.commit()
    assert cliente.get("/ingresos" + FILTRO, headers=headers).status_code == 403
    assert (
        cliente.post("/ingresos", headers=headers, json=entrada(iglesias[0].id)).status_code == 403
    )
    cuentas["tesorero"].activo = False
    sesion.commit()
    assert cliente.get("/ingresos" + FILTRO, headers=headers).status_code == 401
