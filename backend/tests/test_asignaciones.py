"""HU-14: una célula, varios ministerios y líderes que solo quitan en sus grupos."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from test_auth import motor_login as motor_login
from test_usuarios import autorizacion
from test_usuarios import entorno as entorno

from app.modelos import CARGOS, Grupo, GrupoMiembro, Miembro


@pytest.fixture
def equipos(entorno):
    cliente, sesion, cuentas, iglesias, _ = entorno
    personas = [
        Miembro(
            nombre=f"Miembro ficticio {i}",
            iglesia_id=iglesias[0 if i < 4 else 1].id,
            estado="activo",
            telefono="0000000000",
            direccion="Dirección ficticia",
        )
        for i in range(5)
    ]
    sesion.add_all(personas)
    sesion.flush()
    grupos = [
        Grupo(
            nombre="Célula A",
            iglesia_id=iglesias[0].id,
            tipo="celula",
            lider_miembro_id=personas[0].id,
        ),
        Grupo(
            nombre="Célula B",
            iglesia_id=iglesias[0].id,
            tipo="celula",
            lider_miembro_id=personas[1].id,
        ),
        Grupo(
            nombre="Ministerio A",
            iglesia_id=iglesias[0].id,
            tipo="ministerio",
            lider_miembro_id=personas[0].id,
        ),
        Grupo(
            nombre="Ministerio B",
            iglesia_id=iglesias[0].id,
            tipo="ministerio",
            lider_miembro_id=personas[0].id,
        ),
        Grupo(
            nombre="Célula ajena",
            iglesia_id=iglesias[1].id,
            tipo="celula",
            lider_miembro_id=personas[4].id,
        ),
    ]
    sesion.add_all(grupos)
    sesion.flush()
    sesion.add(GrupoMiembro(grupo_id=grupos[0].id, miembro_id=personas[2].id, tipo_grupo="celula"))
    sesion.commit()
    return cliente, sesion, cuentas, iglesias, personas, grupos


def asignacion(grupo, miembro):
    return {"grupo_id": grupo.id, "miembro_id": miembro.id}


def test_segunda_celula_409_y_cambio_tras_quitar_la_anterior(equipos):
    cliente, sesion, cuentas, _, personas, grupos = equipos
    headers = autorizacion(cuentas, "pastor")
    respuesta = cliente.post(
        "/asignaciones", headers=headers, json=asignacion(grupos[1], personas[2])
    )
    assert respuesta.status_code == 409
    assert "célula" in respuesta.json()["detail"]
    assert sesion.get(GrupoMiembro, (grupos[0].id, personas[2].id)) is not None
    assert sesion.get(GrupoMiembro, (grupos[1].id, personas[2].id)) is None
    retirada = cliente.delete(f"/asignaciones/{grupos[0].id}/{personas[2].id}", headers=headers)
    assert retirada.status_code == 204
    assert retirada.content == b""
    respuesta = cliente.post(
        "/asignaciones", headers=headers, json=asignacion(grupos[1], personas[2])
    )
    assert respuesta.status_code == 201, respuesta.text
    assert sesion.get(GrupoMiembro, (grupos[1].id, personas[2].id)).tipo_grupo == "celula"
    assert sesion.get(Miembro, personas[2].id) is not None


def test_varios_ministerios_y_duplicados_sin_tocar_la_celula(equipos):
    cliente, sesion, cuentas, _, personas, grupos = equipos
    headers = autorizacion(cuentas, "apoyo_pastor")
    for grupo in grupos[2:4]:
        respuesta = cliente.post(
            "/asignaciones", headers=headers, json=asignacion(grupo, personas[2])
        )
        assert respuesta.status_code == 201
        assert respuesta.json() == asignacion(grupo, personas[2])
        assert (
            cliente.post(
                "/asignaciones", headers=headers, json=asignacion(grupo, personas[2])
            ).status_code
            == 409
        )
    assert (
        sesion.scalar(
            select(func.count())
            .select_from(GrupoMiembro)
            .where(GrupoMiembro.miembro_id == personas[2].id)
        )
        == 3
    )


@pytest.mark.parametrize("cargo", CARGOS)
def test_solo_gestores_agregan_y_lider_real_solo_quita(equipos, cargo):
    cliente, sesion, cuentas, _, personas, grupos = equipos
    cuentas[cargo].miembro_id = personas[0].id
    sesion.commit()
    headers = autorizacion(cuentas, cargo)
    gestor = cargo in {"presbitero", "pastor", "apoyo_pastor"}
    assert cliente.post(
        "/asignaciones", headers=headers, json=asignacion(grupos[0], personas[3])
    ).status_code == (201 if gestor else 403)
    assert cliente.get(f"/asignaciones/{grupos[0].id}/candidatos", headers=headers).status_code == (
        200 if gestor else 403
    )
    assert cliente.get(f"/asignaciones/{grupos[0].id}", headers=headers).status_code == (
        403 if cargo == "tesorero" else 200
    )
    assert cliente.delete(
        f"/asignaciones/{grupos[0].id}/{personas[2].id}", headers=headers
    ).status_code == (403 if cargo == "tesorero" else 204)


@pytest.mark.parametrize("cargo", ["pastor", "apoyo_pastor", "presbitero", "lider_celula"])
def test_alcance_grupo_real_no_se_cambia_con_query(equipos, cargo):
    cliente, sesion, cuentas, iglesias, personas, grupos = equipos
    cuentas[cargo].miembro_id = personas[0].id
    sesion.add(GrupoMiembro(grupo_id=grupos[1].id, miembro_id=personas[3].id, tipo_grupo="celula"))
    sesion.add(GrupoMiembro(grupo_id=grupos[4].id, miembro_id=personas[4].id, tipo_grupo="celula"))
    sesion.commit()
    headers = autorizacion(cuentas, cargo)
    listado = cliente.get("/asignaciones/grupos", headers=headers)
    assert listado.status_code == 200
    esperados = (
        grupos
        if cargo == "presbitero"
        else grupos[:4]
        if cargo != "lider_celula"
        else [grupos[i] for i in [0, 2, 3]]
    )
    assert {g["id"] for g in listado.json()} == {g.id for g in esperados}
    for indice, miembro in [(1, personas[3]), (4, personas[4])]:
        esperado = (
            200 if cargo == "presbitero" or (indice == 1 and cargo != "lider_celula") else 403
        )
        assert (
            cliente.get(
                f"/asignaciones/{grupos[indice].id}?iglesia_id={iglesias[0].id}", headers=headers
            ).status_code
            == esperado
        )
        assert cliente.delete(
            f"/asignaciones/{grupos[indice].id}/{miembro.id}?iglesia_id={iglesias[0].id}",
            headers=headers,
        ).status_code == (204 if esperado == 200 else 403)


def test_candidatos_minimos_de_la_misma_iglesia_sin_celula_ni_asignados(equipos):
    cliente, _, cuentas, _, personas, grupos = equipos
    headers = autorizacion(cuentas, "pastor")
    respuesta = cliente.get(f"/asignaciones/{grupos[0].id}/candidatos", headers=headers)
    assert respuesta.status_code == 200
    assert {m["id"] for m in respuesta.json()} == {personas[i].id for i in [0, 1, 3]}
    for m in respuesta.json():
        assert set(m) == {"id", "nombre", "estado"}
    assert "0000000000" not in respuesta.text
    assert "Dirección ficticia" not in respuesta.text
    assert personas[2].id in {
        m["id"]
        for m in cliente.get(f"/asignaciones/{grupos[2].id}/candidatos", headers=headers).json()
    }
    integrantes = cliente.get(f"/asignaciones/{grupos[0].id}", headers=headers).json()
    assert integrantes == [{"id": personas[2].id, "nombre": personas[2].nombre, "estado": "activo"}]


@pytest.mark.parametrize("miembro", ["ajeno", "inexistente"])
def test_no_asigna_miembro_de_otra_iglesia_o_inexistente(equipos, miembro):
    cliente, sesion, cuentas, _, personas, grupos = equipos
    datos = {
        "grupo_id": grupos[0].id,
        "miembro_id": personas[4].id if miembro == "ajeno" else 2147483647,
    }
    assert (
        cliente.post(
            "/asignaciones", headers=autorizacion(cuentas, "presbitero"), json=datos
        ).status_code
        == 422
    )
    assert sesion.scalar(select(func.count()).select_from(GrupoMiembro)) == 1


def test_inactivos_solo_gestores_quitan_y_no_se_agrega(equipos):
    cliente, sesion, cuentas, _, personas, grupos = equipos
    cuentas["lider_celula"].miembro_id = personas[0].id
    grupos[0].activo = False
    sesion.commit()
    pastor = autorizacion(cuentas, "pastor")
    lider = autorizacion(cuentas, "lider_celula")
    assert grupos[0].id in {
        g["id"] for g in cliente.get("/asignaciones/grupos", headers=pastor).json()
    }
    assert grupos[0].id not in {
        g["id"] for g in cliente.get("/asignaciones/grupos", headers=lider).json()
    }
    assert cliente.get(f"/asignaciones/{grupos[0].id}", headers=lider).status_code == 403
    assert (
        cliente.post(
            "/asignaciones", headers=pastor, json=asignacion(grupos[0], personas[3])
        ).status_code
        == 422
    )
    assert (
        cliente.get(f"/asignaciones/{grupos[0].id}/candidatos", headers=pastor).status_code == 422
    )
    assert (
        cliente.delete(f"/asignaciones/{grupos[0].id}/{personas[2].id}", headers=pastor).status_code
        == 204
    )


def test_lider_sin_ficha_o_sin_grupo_no_obtiene_candidatos(equipos):
    cliente, _, cuentas, _, _, grupos = equipos
    headers = autorizacion(cuentas, "lider_celula")
    assert cliente.get("/asignaciones/grupos", headers=headers).json() == []
    assert cliente.get(f"/asignaciones/{grupos[0].id}", headers=headers).status_code == 403
    assert (
        cliente.get(f"/asignaciones/{grupos[0].id}/candidatos", headers=headers).status_code == 403
    )


@pytest.mark.parametrize(
    "datos",
    [
        {"grupo_id": 0, "miembro_id": 1},
        {"grupo_id": 1, "miembro_id": 0},
        {"grupo_id": 1, "miembro_id": 1, "tipo_grupo": "ministerio"},
    ],
)
def test_cliente_no_falsifica_tipo_ni_ids(equipos, datos):
    cliente, _, cuentas, _, _, _ = equipos
    assert (
        cliente.post(
            "/asignaciones", headers=autorizacion(cuentas, "pastor"), json=datos
        ).status_code
        == 422
    )


@pytest.mark.parametrize("operacion", ["alta", "retiro"])
def test_fallo_al_confirmar_revierte_la_asignacion(equipos, monkeypatch, operacion):
    cliente, sesion, cuentas, _, personas, grupos = equipos

    def fallo_al_confirmar():
        sesion.flush()
        raise IntegrityError("fallo simulado", {}, Exception("prueba"))

    monkeypatch.setattr(sesion, "commit", fallo_al_confirmar)
    headers = autorizacion(cuentas, "pastor")
    if operacion == "alta":
        respuesta = cliente.post(
            "/asignaciones", headers=headers, json=asignacion(grupos[0], personas[3])
        )
    else:
        respuesta = cliente.delete(
            f"/asignaciones/{grupos[0].id}/{personas[2].id}", headers=headers
        )
    assert respuesta.status_code == 409
    assert sesion.scalar(select(func.count()).select_from(GrupoMiembro)) == 1
    assert sesion.get(GrupoMiembro, (grupos[0].id, personas[2].id)) is not None


def test_sesion_requerida_y_recursos_inexistentes(equipos):
    cliente, _, cuentas, _, personas, grupos = equipos
    assert cliente.get("/asignaciones/grupos").status_code == 401
    assert cliente.get(f"/asignaciones/{grupos[0].id}").status_code == 401
    assert cliente.get(f"/asignaciones/{grupos[0].id}/candidatos").status_code == 401
    assert cliente.post("/asignaciones", json=asignacion(grupos[0], personas[3])).status_code == 401
    assert cliente.delete(f"/asignaciones/{grupos[0].id}/{personas[2].id}").status_code == 401
    headers = autorizacion(cuentas, "pastor")
    assert cliente.get("/asignaciones/2147483647", headers=headers).status_code == 404
    assert (
        cliente.post(
            "/asignaciones",
            headers=headers,
            json={"grupo_id": 2147483647, "miembro_id": personas[3].id},
        ).status_code
        == 404
    )
    assert (
        cliente.delete(
            f"/asignaciones/{grupos[0].id}/{personas[3].id}", headers=headers
        ).status_code
        == 404
    )


def test_cambiar_lider_revoca_retiro_sin_cambiar_token(equipos):
    cliente, sesion, cuentas, _, personas, grupos = equipos
    cuentas["lider_celula"].miembro_id = personas[0].id
    sesion.commit()
    headers = autorizacion(cuentas, "lider_celula")
    assert cliente.get(f"/asignaciones/{grupos[0].id}", headers=headers).status_code == 200
    grupos[0].lider_miembro_id = personas[1].id
    sesion.commit()
    assert (
        cliente.delete(
            f"/asignaciones/{grupos[0].id}/{personas[2].id}", headers=headers
        ).status_code
        == 403
    )
    cuentas["lider_celula"].activo = False
    sesion.commit()
    assert cliente.get("/asignaciones/grupos", headers=headers).status_code == 401
