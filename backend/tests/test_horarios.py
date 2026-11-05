"""HU-05: gestión por sede, alcance por iglesia y contrato público sin datos privados."""

from datetime import time

import pytest
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Horario, RedSocial, Sede
from app.modelos.listas import TIPOS_SERVICIO


def entrada(**cambios):
    return {
        "tipo": "culto_domingo",
        "dia": "domingo",
        "hora_inicio": "10:00",
        "hora_fin": None,
        "descripcion": None,
        **cambios,
    }


@pytest.fixture
def agenda(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    iglesias[0].telefono_pastor = "0000000001"
    iglesias[0].telefono_iglesia = "0000000002"
    sedes = [
        Sede(
            iglesia_id=iglesias[0].id,
            nombre="Sede A",
            direccion="Dirección ficticia A",
            enlace_maps="https://maps.google.com/?q=sede-ficticia",
        ),
        Sede(iglesia_id=iglesias[0].id, nombre="Sede B", direccion="Dirección ficticia B"),
        Sede(iglesia_id=iglesias[1].id, nombre="Sede ajena", direccion="Dirección ficticia C"),
    ]
    sesion.add_all(sedes)
    sesion.add(
        RedSocial(
            iglesia_id=iglesias[0].id,
            nombre="Red ficticia",
            url="https://example.org/red",
            tipo="propia",
        )
    )
    sesion.flush()
    horarios = [
        Horario(sede_id=s.id, tipo="oracion", dia="martes", hora_inicio=time(18)) for s in sedes
    ]
    sesion.add_all(horarios)
    sesion.commit()
    return cliente, sesion, cuentas, iglesias, sedes, horarios


@pytest.mark.parametrize("tipo", TIPOS_SERVICIO)
def test_alta_varios_horarios_del_mismo_tipo_y_horas_locales(agenda, tipo):
    cliente, _, cuentas, _, sedes, _ = agenda
    url = f"/sedes/{sedes[0].id}/horarios"
    headers = autorizacion(cuentas, "pastor")
    for hora in ["10:00", "17:30:00"]:
        respuesta = cliente.post(url, headers=headers, json=entrada(tipo=tipo, hora_inicio=hora))
        assert respuesta.status_code == 201, respuesta.text
        assert respuesta.json()["tipo"] == tipo
        assert respuesta.json()["hora_fin"] is None
        assert respuesta.json()["hora_inicio"] == (hora if len(hora) == 8 else hora + ":00")
    listado = cliente.get(url, headers=headers)
    assert listado.status_code == 200
    assert len([h for h in listado.json() if h["tipo"] == tipo and h["dia"] == "domingo"]) == 2


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor", "presbitero"])
def test_editor_actualiza_y_borra_horario_sin_borrar_sede(agenda, cargo):
    cliente, sesion, cuentas, _, sedes, horarios = agenda
    headers = autorizacion(cuentas, cargo)
    url = f"/horarios/{horarios[0].id}"
    cambios = entrada(dia="viernes", hora_fin="11:30", descripcion="Horario ficticio editado")
    respuesta = cliente.put(url, headers=headers, json=cambios)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["id"] == horarios[0].id
    assert respuesta.json()["dia"] == "viernes"
    assert respuesta.json()["hora_fin"] == "11:30:00"
    assert respuesta.json()["descripcion"] == cambios["descripcion"]
    retirada = cliente.delete(url, headers=headers)
    assert retirada.status_code == 204
    assert retirada.content == b""
    assert sesion.get(Horario, horarios[0].id) is None
    assert sesion.get(Sede, sedes[0].id) is not None
    assert cliente.delete(url, headers=headers).status_code == 404


@pytest.mark.parametrize(
    "cargo", [c for c in CARGOS if c not in {"pastor", "apoyo_pastor", "presbitero"}]
)
def test_otros_cargos_no_gestionan_aunque_conozcan_ids(agenda, cargo):
    cliente, _, cuentas, _, sedes, horarios = agenda
    headers = autorizacion(cuentas, cargo)
    url = f"/sedes/{sedes[0].id}/horarios"
    assert cliente.get("/sedes", headers=headers).status_code == 403
    assert cliente.get(url, headers=headers).status_code == 403
    assert cliente.post(url, headers=headers, json=entrada()).status_code == 403
    assert (
        cliente.put(f"/horarios/{horarios[0].id}", headers=headers, json=entrada()).status_code
        == 403
    )
    assert cliente.delete(f"/horarios/{horarios[0].id}", headers=headers).status_code == 403


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor", "presbitero"])
def test_alcance_usa_iglesia_real_de_sede_y_horario(agenda, cargo):
    cliente, _, cuentas, _, sedes, horarios = agenda
    headers = autorizacion(cuentas, cargo)
    listado = cliente.get("/sedes", headers=headers)
    assert listado.status_code == 200
    assert {s["id"] for s in listado.json()} == {
        s.id for s in sedes if cargo == "presbitero" or s.iglesia_id == cuentas[cargo].iglesia_id
    }
    assert set(listado.json()[0]) == {"id", "nombre", "iglesia_nombre"}
    esperado = 200 if cargo == "presbitero" else 403
    url = f"/sedes/{sedes[2].id}/horarios"
    assert cliente.get(url, headers=headers).status_code == esperado
    assert cliente.post(url, headers=headers, json=entrada()).status_code == (
        201 if esperado == 200 else 403
    )
    # Mandar una iglesia propia en la consulta no cambia la sede real del recurso.
    url_horario = f"/horarios/{horarios[2].id}?iglesia_id={sedes[0].iglesia_id}"
    assert (
        cliente.put(url_horario, headers=headers, json=entrada(hora_inicio="12:00")).status_code
        == esperado
    )
    assert cliente.delete(url_horario, headers=headers).status_code == (
        204 if esperado == 200 else 403
    )


def test_duplicados_409_y_edicion_fallida_no_deja_cambios_parciales(agenda):
    cliente, sesion, cuentas, _, sedes, horarios = agenda
    headers = autorizacion(cuentas, "pastor")
    url = f"/sedes/{sedes[0].id}/horarios"
    duplicado = entrada(tipo="oracion", dia="martes", hora_inicio="18:00")
    assert cliente.post(url, headers=headers, json=duplicado).status_code == 409
    nuevo = cliente.post(url, headers=headers, json=entrada()).json()
    assert (
        cliente.put(f"/horarios/{nuevo['id']}", headers=headers, json=duplicado).status_code == 409
    )
    guardado = sesion.get(Horario, nuevo["id"])
    assert guardado.hora_inicio == time(10)
    assert guardado.dia == "domingo"
    assert sesion.get(Horario, horarios[0].id).hora_inicio == time(18)
    # El propio horario sí se puede guardar sin cambiar su clave única.
    assert (
        cliente.put(f"/horarios/{nuevo['id']}", headers=headers, json=entrada()).status_code == 200
    )


@pytest.mark.parametrize(
    "cambio",
    [
        {"tipo": "otro"},
        {"tipo": "culto"},
        {"dia": "Domingo"},
        {"hora_inicio": "25:00"},
        {"hora_inicio": "10:00Z"},
        {"hora_inicio": "10:00:00-06:00"},
        {"hora_inicio": 3600},
        {"hora_inicio": None},
        {"hora_fin": "09:59"},
        {"hora_fin": "10:00"},
        {"descripcion": "x" * 201},
        {"sede_id": 1},
    ],
)
def test_entrada_invalida_no_se_guarda(agenda, cambio):
    cliente, _, cuentas, _, sedes, _ = agenda
    headers = autorizacion(cuentas, "pastor")
    url = f"/sedes/{sedes[0].id}/horarios"
    assert cliente.post(url, headers=headers, json=entrada(**cambio)).status_code == 422
    assert len(cliente.get(url, headers=headers).json()) == 1


def test_publico_sin_sesion_contrato_y_sin_telefono_personal(agenda, monkeypatch):
    cliente, _, cuentas, iglesias, sedes, _ = agenda
    monkeypatch.delenv("SECRET_KEY")
    respuesta = cliente.get("/publico/iglesias")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos) == 2
    iglesia = next(i for i in datos if i["id"] == iglesias[0].id)
    assert set(iglesia) == {
        "id",
        "nombre",
        "pastor",
        "foto_url",
        "telefono_iglesia",
        "redes",
        "sedes",
    }
    assert iglesia["telefono_iglesia"] == "0000000002"
    assert "0000000001" not in respuesta.text
    assert "telefono_pastor" not in respuesta.text
    assert "contrasena" not in respuesta.text
    assert cuentas["pastor"].nombre_usuario not in respuesta.text
    assert len(iglesia["sedes"]) == 2
    assert iglesia["redes"] == [{"nombre": "Red ficticia", "url": "https://example.org/red"}]
    sede = next(s for s in iglesia["sedes"] if s["id"] == sedes[0].id)
    assert set(sede) == {"id", "nombre", "direccion", "enlace_maps", "horarios"}
    assert sede["direccion"] == "Dirección ficticia A"
    assert set(sede["horarios"][0]) == {
        "id",
        "tipo",
        "dia",
        "hora_inicio",
        "hora_fin",
        "descripcion",
    }


def test_sesion_obligatoria_en_gestion_y_recursos_inexistentes(agenda):
    cliente, _, cuentas, _, sedes, horarios = agenda
    url = f"/sedes/{sedes[0].id}/horarios"
    assert cliente.get("/sedes").status_code == 401
    assert cliente.get(url).status_code == 401
    assert cliente.post(url, json=entrada()).status_code == 401
    assert cliente.put(f"/horarios/{horarios[0].id}", json=entrada()).status_code == 401
    assert cliente.delete(f"/horarios/{horarios[0].id}").status_code == 401
    headers = autorizacion(cuentas, "presbitero")
    assert cliente.get("/sedes/2147483647/horarios", headers=headers).status_code == 404
    assert (
        cliente.post("/sedes/2147483647/horarios", headers=headers, json=entrada()).status_code
        == 404
    )
    assert cliente.put("/horarios/2147483647", headers=headers, json=entrada()).status_code == 404
    assert cliente.delete("/horarios/2147483647", headers=headers).status_code == 404


def test_cambio_de_cargo_en_bd_se_aplica_a_token_existente(agenda):
    cliente, sesion, cuentas, _, sedes, _ = agenda
    headers = autorizacion(cuentas, "pastor")
    cuentas["pastor"].cargo = "tesorero"
    sesion.commit()
    assert (
        cliente.post(f"/sedes/{sedes[0].id}/horarios", headers=headers, json=entrada()).status_code
        == 403
    )
    cuentas["pastor"].activo = False
    sesion.commit()
    assert cliente.get("/sedes", headers=headers).status_code == 401
