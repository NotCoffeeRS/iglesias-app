"""HU-22: sumas exactas, anulados, periodos vacíos y alcance financiero."""

import secrets
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Gasto, Iglesia, Ingreso
from scripts.cargar_datos_ejemplo import (
    GASTOS,
    GASTOS_ANULADOS,
    INGRESOS,
    VARIABLES_CLAVE,
    cargar_datos,
)

RUTA = "/reportes/financiero?desde=2026-11-01&hasta=2026-11-30"


@pytest.fixture
def caja(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    iglesias.extend([Iglesia(nombre="Iglesia ficticia C"), Iglesia(nombre="Iglesia ficticia D")])
    sesion.add_all(iglesias[2:])
    sesion.flush()

    def dinero(modelo, iglesia, monto, **extra):
        valores = {"tipo": "diezmos"} if modelo is Ingreso else {"categoria": "luz"}
        sesion.add(
            modelo(
                iglesia_id=iglesia.id,
                fecha=date(2026, 11, 5),
                monto=Decimal(monto),
                registrado_por=cuentas["presbitero"].id,
                **valores,
                **extra,
            )
        )

    dinero(Ingreso, iglesias[0], "0.10")
    dinero(Ingreso, iglesias[0], "0.20")
    dinero(Gasto, iglesias[0], "0.05")
    dinero(Gasto, iglesias[0], "0.10")
    dinero(Gasto, iglesias[1], "10.00")
    for modelo in [Ingreso, Gasto]:
        dinero(
            modelo,
            iglesias[0],
            "999.00",
            anulado_en=datetime.now(UTC),
            anulado_por=cuentas["pastor"].id,
            anulado_motivo="Registro ficticio anulado",
        )
    sesion.commit()
    return cliente, sesion, cuentas, iglesias


def test_consolidado_cuatro_iglesias_sin_multiplicar_filas_ni_anulados(caja):
    cliente, _, cuentas, iglesias = caja
    r = cliente.get(RUTA, headers=autorizacion(cuentas, "presbitero"))
    assert r.status_code == 200, r.text
    datos = r.json()
    assert len(datos["iglesias"]) == 4
    total = datos["consolidado"]
    assert (total["ingresos"], total["gastos"], total["balance"]) == ("0.30", "10.15", "-9.85")
    fila = next(i for i in datos["iglesias"] if i["iglesia_id"] == iglesias[0].id)
    assert (fila["ingresos"], fila["gastos"], fila["balance"]) == ("0.30", "0.15", "0.15")
    assert next(p["monto"] for p in fila["ingresos_por_tipo"] if p["clave"] == "diezmos") == "0.30"
    assert sum(Decimal(p["monto"]) for p in total["gastos_por_categoria"]) == Decimal("10.15")
    assert "Registro ficticio anulado" not in r.text


@pytest.mark.parametrize("cargo", ["pastor", "tesorero", "presbitero"])
def test_alcance_y_consolidado_solo_presbitero_sin_filtro(caja, cargo):
    cliente, _, cuentas, iglesias = caja
    headers = autorizacion(cuentas, cargo)
    datos = cliente.get(RUTA, headers=headers).json()
    assert len(datos["iglesias"]) == (4 if cargo == "presbitero" else 1)
    if cargo != "presbitero":
        assert datos["consolidado"] is None
        assert datos["iglesias"][0]["iglesia_id"] == iglesias[0].id
    filtrado = cliente.get(RUTA + f"&iglesia_id={iglesias[1].id}", headers=headers)
    assert filtrado.status_code == (200 if cargo == "presbitero" else 403)
    if cargo == "presbitero":
        assert filtrado.json()["consolidado"] is None
        assert filtrado.json()["iglesias"][0]["balance"] == "-10.00"


@pytest.mark.parametrize(
    "cargo", [c for c in CARGOS if c not in {"pastor", "tesorero", "presbitero"}]
)
def test_otros_cargos_no_ven_dinero(caja, cargo):
    cliente, _, cuentas, iglesias = caja
    for filtro in ["", f"&iglesia_id={iglesias[0].id}"]:
        assert cliente.get(RUTA + filtro, headers=autorizacion(cuentas, cargo)).status_code == 403


def test_periodo_vacio_y_limites_inclusivos(caja):
    cliente, _, cuentas, _ = caja
    headers = autorizacion(cuentas, "presbitero")
    vacio = cliente.get(
        "/reportes/financiero?desde=2026-12-01&hasta=2026-12-31", headers=headers
    ).json()
    assert len(vacio["iglesias"]) == 4
    for fila in [vacio["consolidado"], *vacio["iglesias"]]:
        assert fila["ingresos"] == fila["gastos"] == fila["balance"] == "0.00"
        assert all(
            p["monto"] == "0.00" for p in fila["ingresos_por_tipo"] + fila["gastos_por_categoria"]
        )
    limites = cliente.get(
        "/reportes/financiero?desde=2026-11-05&hasta=2026-11-05", headers=headers
    ).json()
    assert limites["consolidado"]["balance"] == "-9.85"


def test_validacion_sesion_y_revocacion(caja):
    cliente, sesion, cuentas, _ = caja
    assert cliente.get(RUTA).status_code == 401
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.get(RUTA + "&iglesia_id=2147483647", headers=headers).status_code == 404
    assert cliente.get(RUTA + "&iglesia_id=0", headers=headers).status_code == 422
    assert (
        cliente.get(
            "/reportes/financiero?desde=2026-12-01&hasta=2026-11-01", headers=headers
        ).status_code
        == 422
    )
    assert cliente.get("/reportes/financiero", headers=headers).status_code == 422
    headers = autorizacion(cuentas, "tesorero")
    cuentas["tesorero"].cargo = "apoyo_pastor"
    sesion.commit()
    assert cliente.get(RUTA, headers=headers).status_code == 403
    cuentas["tesorero"].activo = False
    sesion.commit()
    assert cliente.get(RUTA, headers=headers).status_code == 401


def test_datos_de_ejemplo_del_proyecto(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    cargar_datos(sesion, {cargo: secrets.token_urlsafe(24) for cargo in VARIABLES_CLAVE})
    sesion.commit()
    r = cliente.get(
        "/reportes/financiero?desde=2026-10-01&hasta=2026-11-30",
        headers=autorizacion(cuentas, "presbitero"),
    )
    assert r.status_code == 200, r.text
    datos = r.json()
    esperado_ingresos = sum((Decimal(i[4]) for i in INGRESOS), Decimal("0"))
    esperado_gastos = sum(
        (Decimal(g[4]) for g in GASTOS if g[0] not in GASTOS_ANULADOS), Decimal("0")
    )
    assert Decimal(datos["consolidado"]["ingresos"]) == esperado_ingresos
    assert Decimal(datos["consolidado"]["gastos"]) == esperado_gastos
    assert Decimal(datos["consolidado"]["balance"]) == esperado_ingresos - esperado_gastos
    for fila in datos["iglesias"]:
        assert Decimal(fila["balance"]) == Decimal(fila["ingresos"]) - Decimal(fila["gastos"])
    assert len(list(sesion.scalars(select(Iglesia)))) == len(datos["iglesias"])
