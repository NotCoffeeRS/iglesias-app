"""HU-03: contratos, dos sedes, atomicidad y permisos sobre PostgreSQL migrado."""

from copy import deepcopy
from datetime import time

import pytest
from sqlalchemy import select
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Horario, Iglesia, RedSocial, Sede


def entrada(**cambios):
    return {
        "nombre": "Iglesia de prueba con dos sedes",
        "foto_url": "https://example.org/fachada.jpg",
        "pastor": "Pastor ficticio",
        "telefono_pastor": None,
        "telefono_iglesia": None,
        "sedes": [
            {
                "nombre": "Sede A",
                "direccion": "Dirección ficticia A",
                "enlace_maps": "https://maps.google.com/?q=sede-ficticia",
            },
            {"nombre": "Sede B", "direccion": "Dirección ficticia B"},
        ],
        "redes": [
            {"nombre": "Red propia", "url": "https://example.org/propia", "tipo": "propia"},
            {"nombre": "Red amiga", "url": "https://example.org/amiga", "tipo": "relacionada"},
        ],
        **cambios,
    }


def alta(entorno):
    cliente, _, cuentas, _, _ = entorno
    resultado = cliente.post(
        "/iglesias", headers=autorizacion(cuentas, "presbitero"), json=entrada()
    )
    assert resultado.status_code == 201, resultado.text
    return resultado.json()


def cuerpo(respuesta):
    return deepcopy({k: v for k, v in respuesta.items() if k != "id"})


def test_alta_dos_sedes_telefonos_opcionales_y_varias_redes(entorno):
    cliente, _, cuentas, _, _ = entorno
    creada = alta(entorno)
    assert len(creada["sedes"]) == 2
    assert {r["tipo"] for r in creada["redes"]} == {"propia", "relacionada"}
    assert creada["telefono_pastor"] is None
    assert creada["telefono_iglesia"] is None
    detalle = cliente.get(f"/iglesias/{creada['id']}", headers=autorizacion(cuentas, "presbitero"))
    assert detalle.json() == creada
    resumen = cliente.get("/iglesias", headers=autorizacion(cuentas, "presbitero")).json()
    fila = next(i for i in resumen if i["id"] == creada["id"])
    assert fila["total_sedes"] == 2
    assert "telefono_pastor" not in fila


@pytest.mark.parametrize("cargo", [c for c in CARGOS if c != "presbitero"])
def test_alta_solo_presbitero(entorno, cargo):
    cliente, _, cuentas, _, _ = entorno
    assert (
        cliente.post("/iglesias", headers=autorizacion(cuentas, cargo), json=entrada()).status_code
        == 403
    )


@pytest.mark.parametrize("cargo", CARGOS)
def test_edicion_por_cargo_y_lectura_limitada_a_iglesia(entorno, cargo):
    cliente, _, cuentas, iglesias, _ = entorno
    headers = autorizacion(cuentas, cargo)
    resumen = cliente.get("/iglesias", headers=headers)
    assert resumen.status_code == 200
    assert {i["id"] for i in resumen.json()} == {
        i.id for i in iglesias if cargo == "presbitero" or i.id == iglesias[0].id
    }
    assert cliente.get(f"/iglesias/{iglesias[0].id}", headers=headers).status_code == 200
    respuesta = cliente.put(f"/iglesias/{iglesias[0].id}", headers=headers, json=entrada())
    assert respuesta.status_code == (
        200 if cargo in {"pastor", "apoyo_pastor", "presbitero"} else 403
    )


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor"])
def test_no_consulta_ni_edita_iglesia_ajena(entorno, cargo):
    cliente, _, cuentas, iglesias, _ = entorno
    headers = autorizacion(cuentas, cargo)
    url = f"/iglesias/{iglesias[1].id}"
    assert cliente.get(url, headers=headers).status_code == 403
    assert cliente.put(url, headers=headers, json=entrada()).status_code == 403


def test_presbitero_edita_cualquier_iglesia_y_conserva_ids(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    headers = autorizacion(cuentas, "presbitero")
    url = f"/iglesias/{iglesias[1].id}"
    inicial = cliente.put(url, headers=headers, json=entrada()).json()
    cambios = cuerpo(inicial)
    cambios["nombre"] = "Nombre editado"
    cambios["telefono_iglesia"] = "0000000000"
    cambios["sedes"][0]["direccion"] = "Otra dirección ficticia"
    cambios["sedes"][0]["nombre"], cambios["sedes"][1]["nombre"] = (
        cambios["sedes"][1]["nombre"],
        cambios["sedes"][0]["nombre"],
    )
    cambios["redes"][0]["nombre"] = "Red editada"
    respuesta = cliente.put(url, headers=headers, json=cambios)
    assert respuesta.status_code == 200, respuesta.text
    final = respuesta.json()
    assert final["telefono_iglesia"] == "0000000000"
    assert final["nombre"] == "Nombre editado"
    assert [s["id"] for s in final["sedes"]] == [s["id"] for s in inicial["sedes"]]
    assert final["sedes"][0]["nombre"] == "Sede B"
    assert final["redes"][0]["id"] == inicial["redes"][0]["id"]
    assert final["redes"][0]["nombre"] == "Red editada"


def test_listas_completas_quitan_sin_referencias_y_agregan_hijos(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    creada = alta(entorno)
    cambios = cuerpo(creada)
    sede_retirada = cambios["sedes"].pop()
    red_retirada = cambios["redes"].pop()
    cambios["sedes"].append({"nombre": "Sede nueva", "direccion": "Dirección ficticia nueva"})
    cambios["redes"].append(
        {"nombre": "Nueva", "url": "https://example.org/nueva", "tipo": "propia"}
    )
    resultado = cliente.put(
        f"/iglesias/{creada['id']}", headers=autorizacion(cuentas, "presbitero"), json=cambios
    )
    assert resultado.status_code == 200, resultado.text
    assert sesion.get(Sede, sede_retirada["id"]) is None
    assert sesion.get(RedSocial, red_retirada["id"]) is None
    assert len(resultado.json()["sedes"]) == 2


def test_sede_con_horarios_no_se_quita_y_no_hay_cambios_parciales(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    creada = alta(entorno)
    horario = Horario(
        sede_id=creada["sedes"][1]["id"], tipo="culto_domingo", dia="domingo", hora_inicio=time(10)
    )
    sesion.add(horario)
    sesion.commit()
    cambios = cuerpo(creada)
    cambios["sedes"] = cambios["sedes"][:1]
    cambios["nombre"] = "Este cambio no debe guardarse"
    cambios["redes"] = []
    url = f"/iglesias/{creada['id']}"
    headers = autorizacion(cuentas, "presbitero")
    resultado = cliente.put(url, headers=headers, json=cambios)
    assert resultado.status_code == 409
    assert "horarios" in resultado.json()["detail"]
    assert cliente.get(url, headers=headers).json() == creada
    assert sesion.get(Horario, horario.id) is not None


@pytest.mark.parametrize("coleccion,modelo", [("sedes", Sede), ("redes", RedSocial)])
def test_hijos_ajenos_o_inexistentes_no_se_reasignan(entorno, coleccion, modelo):
    cliente, sesion, cuentas, iglesias, _ = entorno
    creada = alta(entorno)
    valores = (
        {"nombre": "Ajena", "direccion": "Dirección ficticia"}
        if modelo is Sede
        else {"nombre": "Ajena", "url": "https://example.org/ajena", "tipo": "propia"}
    )
    ajeno = modelo(iglesia_id=iglesias[0].id, **valores)
    sesion.add(ajeno)
    sesion.commit()
    headers = autorizacion(cuentas, "presbitero")
    url = f"/iglesias/{creada['id']}"
    for identificador in [ajeno.id, 2147483647]:
        cambios = cuerpo(creada)
        cambios[coleccion] = [{"id": identificador, **valores}]
        assert cliente.put(url, headers=headers, json=cambios).status_code == 403
        assert cliente.get(url, headers=headers).json() == creada
    assert sesion.get(modelo, ajeno.id).iglesia_id == iglesias[0].id


def test_nombre_duplicado_409_y_rollback_incluye_sedes(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    creada = alta(entorno)
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.post("/iglesias", headers=headers, json=entrada()).status_code == 409
    cambios = cuerpo(creada)
    cambios["nombre"] = iglesias[0].nombre
    cambios["sedes"][0]["direccion"] = "Cambio descartado"
    url = f"/iglesias/{creada['id']}"
    assert cliente.put(url, headers=headers, json=cambios).status_code == 409
    assert cliente.get(url, headers=headers).json() == creada
    assert len(list(sesion.scalars(select(Iglesia)))) == 3


@pytest.mark.parametrize(
    "cambio",
    [
        {"sedes": []},
        {"nombre": "   "},
        {"foto_url": "javascript:alert(1)"},
        {"telefono_pastor": "0" * 21},
        {"cargo": "presbitero"},
        {"sedes": [{"nombre": "A", "direccion": " "}]},
        {"redes": [{"nombre": "A", "url": "https://example.org", "tipo": "otra"}]},
        {
            "sedes": [
                {"id": 1, "nombre": "A", "direccion": "A"},
                {"id": 1, "nombre": "B", "direccion": "B"},
            ]
        },
        {"sedes": [{"nombre": "A", "direccion": "A"}, {"nombre": " A ", "direccion": "B"}]},
    ],
)
def test_entrada_invalida_422_sin_reflejar_datos(entorno, cambio):
    cliente, _, cuentas, _, _ = entorno
    resultado = cliente.post(
        "/iglesias", headers=autorizacion(cuentas, "presbitero"), json=entrada(**cambio)
    )
    assert resultado.status_code == 422
    assert "input" not in resultado.text
    assert "Pastor ficticio" not in resultado.text


def test_sesion_obligatoria_y_404_para_presbitero(entorno):
    cliente, _, cuentas, iglesias, _ = entorno
    assert cliente.get("/iglesias").status_code == 401
    assert cliente.get(f"/iglesias/{iglesias[0].id}").status_code == 401
    assert cliente.post("/iglesias", json=entrada()).status_code == 401
    assert cliente.put(f"/iglesias/{iglesias[0].id}", json=entrada()).status_code == 401
    assert (
        cliente.get("/iglesias/2147483647", headers=autorizacion(cuentas, "presbitero")).status_code
        == 404
    )


def test_editar_sede_conserva_sus_horarios(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    creada = alta(entorno)
    horario = Horario(
        sede_id=creada["sedes"][0]["id"],
        tipo="culto_domingo",
        dia="domingo",
        hora_inicio=time(10),
    )
    sesion.add(horario)
    sesion.commit()
    cambios = cuerpo(creada)
    cambios["sedes"][0]["nombre"] = "Sede con otro nombre"
    cambios["sedes"][0]["direccion"] = "Dirección actualizada ficticia"
    resultado = cliente.put(
        f"/iglesias/{creada['id']}",
        headers=autorizacion(cuentas, "presbitero"),
        json=cambios,
    )
    assert resultado.status_code == 200, resultado.text
    assert resultado.json()["sedes"][0]["nombre"] == "Sede con otro nombre"
    assert sesion.get(Horario, horario.id).sede_id == creada["sedes"][0]["id"]


def test_alta_no_adopta_identificadores_y_cuenta_inactiva_no_accede(entorno):
    cliente, sesion, cuentas, _, _ = entorno
    datos = entrada()
    datos["sedes"][0]["id"] = 1
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.post("/iglesias", headers=headers, json=datos).status_code == 422
    cuentas["presbitero"].activo = False
    sesion.commit()
    assert cliente.get("/iglesias", headers=headers).status_code == 401
