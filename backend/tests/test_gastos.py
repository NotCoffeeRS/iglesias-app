"""HU-17: categorías, dinero exacto, anulación y alcance financiero con PostgreSQL."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Gasto
from app.modelos.listas import CATEGORIAS_GASTO

FILTRO = "?desde=2026-11-01&hasta=2026-11-30"


def entrada(iglesia_id, **cambios):
    return {
        "iglesia_id": iglesia_id,
        "fecha": "2026-11-05",
        "categoria": "luz",
        "monto": "100.50",
        "nota": None,
        **cambios,
    }


@pytest.fixture
def caja(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    gastos = [
        Gasto(
            iglesia_id=i.id,
            fecha=date(2026, 11, 5),
            categoria="agua",
            monto=Decimal("25.00"),
            registrado_por=cuentas["presbitero"].id,
        )
        for i in iglesias
    ]
    sesion.add_all(gastos)
    sesion.commit()
    return cliente, sesion, cuentas, iglesias, gastos


@pytest.mark.parametrize("categoria", CATEGORIAS_GASTO)
def test_alta_categorias_contrato_y_nota_opcional(entorno, categoria):
    cliente, sesion, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/gastos",
        headers=autorizacion(cuentas, "tesorero"),
        json=entrada(iglesias[0].id, categoria=categoria),
    )
    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    assert set(datos) == {
        "id",
        "iglesia_id",
        "iglesia_nombre",
        "fecha",
        "categoria",
        "monto",
        "nota",
        "anulado",
        "motivo_anulacion",
    }
    assert datos["monto"] == "100.50"
    assert datos["categoria"] == categoria
    assert datos["iglesia_nombre"] == iglesias[0].nombre
    assert datos["anulado"] is False
    assert datos["motivo_anulacion"] is None
    assert datos["nota"] is None
    assert sesion.get(Gasto, datos["id"]).registrado_por == cuentas["tesorero"].id


@pytest.mark.parametrize(
    "monto,esperado",
    [
        ("0.01", "0.01"),
        ("1500", "1500.00"),
        ("1500.5", "1500.50"),
        ("9999999999.99", "9999999999.99"),
    ],
)
def test_limites_monetarios_sin_redondeo(entorno, monto, esperado):
    cliente, sesion, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/gastos",
        headers=autorizacion(cuentas, "pastor"),
        json=entrada(iglesias[0].id, monto=monto, nota="Gasto ficticio"),
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["monto"] == esperado
    assert respuesta.json()["nota"] == "Gasto ficticio"
    assert sesion.get(Gasto, respuesta.json()["id"]).monto == Decimal(esperado)


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
def test_monto_invalido_no_se_guarda_ni_refleja_datos(entorno, monto):
    cliente, sesion, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/gastos",
        headers=autorizacion(cuentas, "tesorero"),
        json=entrada(iglesias[0].id, monto=monto, nota="Nota ficticia privada"),
    )
    assert respuesta.status_code == 422
    assert sesion.scalar(select(func.count()).select_from(Gasto)) == 0
    assert "input" not in respuesta.text
    assert "Nota ficticia privada" not in respuesta.text


@pytest.mark.parametrize(
    "cambios",
    [
        {"categoria": "otra"},
        {"categoria": ""},
        {"fecha": "2026-02-30"},
        {"registrado_por": 1},
        {"anulado": True},
        {"anulado_por": 1},
    ],
)
def test_categoria_cerrada_y_no_se_falsifica_estado_ni_auditoria(entorno, cambios):
    cliente, sesion, cuentas, iglesias, _ = entorno
    respuesta = cliente.post(
        "/gastos",
        headers=autorizacion(cuentas, "presbitero"),
        json=entrada(iglesias[0].id, **cambios),
    )
    assert respuesta.status_code == 422
    assert sesion.scalar(select(func.count()).select_from(Gasto)) == 0


@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "presbitero"])
def test_anular_con_motivo_conserva_gasto_y_auditoria(caja, cargo):
    cliente, sesion, cuentas, _, gastos = caja
    headers = autorizacion(cuentas, cargo)
    url = f"/gastos/{gastos[0].id}/anular"
    respuesta = cliente.post(url, headers=headers, json={"motivo": "  Gasto ficticio duplicado  "})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["anulado"] is True
    assert respuesta.json()["motivo_anulacion"] == "Gasto ficticio duplicado"
    assert respuesta.json()["monto"] == "25.00"
    guardado = sesion.get(Gasto, gastos[0].id)
    assert guardado.anulado_por == cuentas[cargo].id
    assert guardado.registrado_por == cuentas["presbitero"].id
    assert guardado.anulado_en is not None
    instante = guardado.anulado_en
    assert cliente.post(url, headers=headers, json={"motivo": "Reemplazo"}).status_code == 409
    assert sesion.get(Gasto, gastos[0].id).anulado_en == instante
    assert guardado.anulado_motivo == "Gasto ficticio duplicado"
    listado = cliente.get("/gastos" + FILTRO, headers=headers).json()
    assert next(g for g in listado if g["id"] == gastos[0].id)["anulado"] is True
    assert cliente.delete(f"/gastos/{gastos[0].id}", headers=headers).status_code in {404, 405}
    assert sesion.get(Gasto, gastos[0].id) is not None


@pytest.mark.parametrize(
    "datos", [{}, {"motivo": ""}, {"motivo": "   "}, {"motivo": "Ficticio", "anulado_por": 1}]
)
def test_anulacion_exige_motivo_y_auditoria_del_servidor(caja, datos):
    cliente, sesion, cuentas, _, gastos = caja
    respuesta = cliente.post(
        f"/gastos/{gastos[0].id}/anular", headers=autorizacion(cuentas, "tesorero"), json=datos
    )
    assert respuesta.status_code == 422
    assert sesion.get(Gasto, gastos[0].id).anulado_en is None


@pytest.mark.parametrize(
    "cargo", [c for c in CARGOS if c not in {"pastor", "tesorero", "presbitero"}]
)
def test_cargos_sin_dinero_no_consultan_registran_ni_anulan(caja, cargo):
    cliente, _, cuentas, iglesias, gastos = caja
    headers = autorizacion(cuentas, cargo)
    assert cliente.get("/gastos" + FILTRO, headers=headers).status_code == 403
    assert cliente.post("/gastos", headers=headers, json=entrada(iglesias[0].id)).status_code == 403
    assert (
        cliente.post(
            f"/gastos/{gastos[0].id}/anular", headers=headers, json={"motivo": "Ficticio"}
        ).status_code
        == 403
    )


@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "presbitero"])
def test_alcance_por_iglesia_real_y_alta_con_auditoria(caja, cargo):
    cliente, sesion, cuentas, iglesias, gastos = caja
    headers = autorizacion(cuentas, cargo)
    listado = cliente.get("/gastos" + FILTRO, headers=headers)
    assert listado.status_code == 200
    assert {g["iglesia_id"] for g in listado.json()} == {
        i.id for i in iglesias if cargo == "presbitero" or i.id == iglesias[0].id
    }
    propia = cliente.post("/gastos", headers=headers, json=entrada(iglesias[0].id))
    assert propia.status_code == 201
    assert sesion.get(Gasto, propia.json()["id"]).registrado_por == cuentas[cargo].id
    esperado = 200 if cargo == "presbitero" else 403
    assert (
        cliente.get(
            "/gastos" + FILTRO + f"&iglesia_id={iglesias[1].id}", headers=headers
        ).status_code
        == esperado
    )
    assert cliente.post("/gastos", headers=headers, json=entrada(iglesias[1].id)).status_code == (
        201 if esperado == 200 else 403
    )
    assert (
        cliente.post(
            f"/gastos/{gastos[1].id}/anular?iglesia_id={iglesias[0].id}",
            headers=headers,
            json={"motivo": "Ficticio"},
        ).status_code
        == esperado
    )


def test_filtros_inclusivos_validacion_y_vacios(caja):
    cliente, _, cuentas, iglesias, _ = caja
    headers = autorizacion(cuentas, "presbitero")
    url = f"/gastos?desde=2026-11-05&hasta=2026-11-05&iglesia_id={iglesias[0].id}"
    assert len(cliente.get(url, headers=headers).json()) == 1
    assert cliente.get("/gastos?desde=2026-11-06&hasta=2026-11-30", headers=headers).json() == []
    assert (
        cliente.get("/gastos?desde=2026-11-30&hasta=2026-11-01", headers=headers).status_code == 422
    )
    assert (
        cliente.get("/gastos?desde=no-fecha&hasta=2026-11-30", headers=headers).status_code == 422
    )
    assert cliente.get("/gastos", headers=headers).status_code == 422
    assert cliente.get("/gastos" + FILTRO + "&iglesia_id=0", headers=headers).status_code == 422


@pytest.mark.parametrize("operacion", ["registro", "anulacion"])
def test_fallo_al_confirmar_no_deja_datos_parciales(caja, monkeypatch, operacion):
    cliente, sesion, cuentas, iglesias, gastos = caja

    def fallo_al_confirmar():
        sesion.flush()
        raise IntegrityError("fallo simulado de prueba", {}, Exception("prueba"))

    monkeypatch.setattr(sesion, "commit", fallo_al_confirmar)
    headers = autorizacion(cuentas, "tesorero")
    if operacion == "registro":
        respuesta = cliente.post("/gastos", headers=headers, json=entrada(iglesias[0].id))
    else:
        respuesta = cliente.post(
            f"/gastos/{gastos[0].id}/anular", headers=headers, json={"motivo": "Ficticio"}
        )
    assert respuesta.status_code == 409
    assert sesion.scalar(select(func.count()).select_from(Gasto)) == 2
    guardado = sesion.get(Gasto, gastos[0].id)
    assert guardado.anulado_en is None
    assert guardado.anulado_por is None
    assert guardado.anulado_motivo is None


def test_sesion_requerida_y_404_en_recursos_inexistentes(caja):
    cliente, _, cuentas, iglesias, gastos = caja
    assert cliente.get("/gastos" + FILTRO).status_code == 401
    assert cliente.post("/gastos", json=entrada(iglesias[0].id)).status_code == 401
    assert (
        cliente.post(f"/gastos/{gastos[0].id}/anular", json={"motivo": "Ficticio"}).status_code
        == 401
    )
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.post("/gastos", headers=headers, json=entrada(2147483647)).status_code == 404
    assert (
        cliente.get("/gastos" + FILTRO + "&iglesia_id=2147483647", headers=headers).status_code
        == 404
    )
    assert (
        cliente.post(
            "/gastos/2147483647/anular", headers=headers, json={"motivo": "Ficticio"}
        ).status_code
        == 404
    )


def test_revocacion_de_cargo_y_cuenta_inactiva_se_aplican_al_token(caja):
    cliente, sesion, cuentas, iglesias, _ = caja
    headers = autorizacion(cuentas, "tesorero")
    cuentas["tesorero"].cargo = "apoyo_pastor"
    sesion.commit()
    assert cliente.get("/gastos" + FILTRO, headers=headers).status_code == 403
    assert cliente.post("/gastos", headers=headers, json=entrada(iglesias[0].id)).status_code == 403
    cuentas["tesorero"].activo = False
    sesion.commit()
    assert cliente.get("/gastos" + FILTRO, headers=headers).status_code == 401
