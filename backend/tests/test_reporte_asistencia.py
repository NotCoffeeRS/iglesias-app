"""HU-21: alcance actual, marcas sin duplicar y ausencia de datos inventados."""

import secrets
from datetime import date

import pytest
from sqlalchemy import select
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Asistencia, Grupo, GrupoMiembro, Miembro
from scripts.cargar_datos_ejemplo import VARIABLES_CLAVE, cargar_datos

RUTA = "/reportes/asistencia?desde=2026-11-01&hasta=2026-11-30"


@pytest.fixture
def marcas(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    personas = [
        Miembro(
            nombre=f"Persona ficticia {i}",
            iglesia_id=iglesias[i == 4].id,
            estado="inactivo" if i == 3 else "activo",
        )
        for i in range(5)
    ]
    sesion.add_all(personas)
    sesion.flush()
    grupos = [
        Grupo(
            nombre=f"Grupo ficticio {i}",
            tipo="celula" if i == 0 else "ministerio",
            iglesia_id=iglesias[0].id,
            lider_miembro_id=personas[0].id,
        )
        for i in range(2)
    ]
    sesion.add_all(grupos)
    sesion.flush()
    for g in grupos:
        sesion.add(GrupoMiembro(grupo_id=g.id, miembro_id=personas[1].id, tipo_grupo=g.tipo))
    for i in [1, 2, 3, 4]:
        sesion.add(
            Asistencia(
                miembro_id=personas[i].id,
                fecha=date(2026, 11, 5),
                tipo_servicio="culto_domingo",
                presente=i != 2,
                registrado_por=cuentas["presbitero"].id,
            )
        )
    sesion.add(
        Asistencia(
            miembro_id=personas[1].id,
            fecha=date(2026, 11, 6),
            tipo_servicio="otro",
            presente=False,
            registrado_por=cuentas["presbitero"].id,
        )
    )
    sesion.commit()
    return cliente, sesion, cuentas, iglesias, personas, grupos


@pytest.mark.parametrize("cargo", CARGOS)
def test_alcance_por_cargo_y_sin_doble_conteo_por_varios_grupos(marcas, cargo):
    cliente, sesion, cuentas, _, personas, _ = marcas
    cuentas[cargo].miembro_id = personas[0].id
    sesion.commit()
    r = cliente.get(RUTA, headers=autorizacion(cuentas, cargo))
    if cargo == "tesorero":
        assert r.status_code == 403
        return
    assert r.status_code == 200, r.text
    esperado = (
        (5, 3, 2)
        if cargo == "presbitero"
        else (4, 2, 2)
        if cargo in {"pastor", "apoyo_pastor"}
        else (1, 0, 1)
        if cargo == "ujier"
        else (2, 1, 1)
    )
    t = r.json()["totales"]
    assert (t["registros"], t["asistencias"], t["faltas"]) == esperado
    assert "Persona ficticia" not in r.text
    assert "miembro_id" not in r.text


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor", "lider_celula", "ujier"])
def test_no_consulta_otra_iglesia(marcas, cargo):
    cliente, _, cuentas, iglesias, _, _ = marcas
    assert (
        cliente.get(
            RUTA + f"&iglesia_id={iglesias[1].id}", headers=autorizacion(cuentas, cargo)
        ).status_code
        == 403
    )


def test_presbitero_filtra_iglesia_periodo_y_servicio(marcas):
    cliente, _, cuentas, iglesias, _, _ = marcas
    headers = autorizacion(cuentas, "presbitero")
    r = cliente.get(RUTA + f"&iglesia_id={iglesias[1].id}", headers=headers).json()
    assert len(r["iglesias"]) == 1
    assert r["totales"] == {"registros": 1, "asistencias": 1, "faltas": 0}
    r = cliente.get(RUTA + "&servicio=otro", headers=headers).json()
    assert r["totales"] == {"registros": 1, "asistencias": 0, "faltas": 1}
    r = cliente.get(
        "/reportes/asistencia?desde=2026-11-05&hasta=2026-11-05", headers=headers
    ).json()
    assert r["totales"]["registros"] == 4
    assert all(d["fecha"] == "2026-11-05" for i in r["iglesias"] for d in i["detalle"])


def test_sin_marcas_no_se_inventan_faltas(marcas):
    cliente, _, cuentas, _, _, _ = marcas
    r = cliente.get(
        "/reportes/asistencia?desde=2026-12-01&hasta=2026-12-31",
        headers=autorizacion(cuentas, "presbitero"),
    ).json()
    assert r["totales"] == {"registros": 0, "asistencias": 0, "faltas": 0}
    assert len(r["iglesias"]) == 2
    assert all(i["detalle"] == [] and i["registros"] == 0 for i in r["iglesias"])


def test_lider_sin_ficha_y_cambio_de_asignaciones_actuales(marcas):
    cliente, sesion, cuentas, _, personas, grupos = marcas
    headers = autorizacion(cuentas, "lider_celula")
    assert cliente.get(RUTA, headers=headers).json()["totales"]["registros"] == 0
    cuentas["lider_celula"].miembro_id = personas[0].id
    sesion.commit()
    assert cliente.get(RUTA, headers=headers).json()["totales"]["registros"] == 2
    for g in grupos:
        g.activo = False
    sesion.commit()
    assert cliente.get(RUTA, headers=headers).json()["totales"]["registros"] == 0
    sesion.add(GrupoMiembro(grupo_id=grupos[0].id, miembro_id=personas[2].id, tipo_grupo="celula"))
    sesion.commit()
    assert (
        cliente.get(RUTA, headers=autorizacion(cuentas, "ujier")).json()["totales"]["registros"]
        == 0
    )


def test_validacion_sesion_y_cuenta_inactiva(marcas):
    cliente, sesion, cuentas, _, _, _ = marcas
    assert cliente.get(RUTA).status_code == 401
    headers = autorizacion(cuentas, "presbitero")
    for url in [
        RUTA + "&servicio=inventado",
        RUTA + "&iglesia_id=0",
        "/reportes/asistencia",
        "/reportes/asistencia?desde=2026-11-30&hasta=2026-11-01",
    ]:
        assert cliente.get(url, headers=headers).status_code == 422
    assert cliente.get(RUTA + "&iglesia_id=2147483647", headers=headers).status_code == 404
    cuentas["presbitero"].activo = False
    sesion.commit()
    assert cliente.get(RUTA, headers=headers).status_code == 401


def test_datos_de_ejemplo_y_marcas_ficticias(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    cargar_datos(sesion, {c: secrets.token_urlsafe(24) for c in VARIABLES_CLAVE})
    sesion.commit()
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.get(RUTA, headers=headers).json()["totales"]["registros"] == 0
    persona = sesion.scalar(select(Miembro).order_by(Miembro.id))
    sesion.add(
        Asistencia(
            miembro_id=persona.id,
            fecha=date(2026, 11, 5),
            tipo_servicio="oracion",
            presente=True,
            registrado_por=cuentas["presbitero"].id,
        )
    )
    sesion.commit()
    datos = cliente.get(RUTA, headers=headers).json()
    assert datos["totales"] == {"registros": 1, "asistencias": 1, "faltas": 0}
    assert len(datos["iglesias"]) == 6
