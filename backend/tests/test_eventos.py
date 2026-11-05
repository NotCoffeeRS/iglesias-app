"""API de eventos contra un PostgreSQL temporal migrado con Alembic (Issue #32, D9 y D20).

Todos los nombres, cargos y fechas son inventados.
"""

import secrets
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from alembic import command
from app.db import get_db
from app.main import crear_app
from app.modelos import Evento, Iglesia, Usuario
from app.modelos.utilidades import obtener_url_base_datos
from app.modulos.eventos.servicio import hoy_en_merida
from app.seguridad.contrasenas import crear_hash
from app.seguridad.tokens import crear_token

HOY = hoy_en_merida()
MANANA = HOY + timedelta(days=1)
PASADO = HOY + timedelta(days=2)
AYER = HOY - timedelta(days=1)


@pytest.fixture(scope="module")
def motor():
    """Crea y borra su propia base temporal; nunca migra la base configurada."""
    url_texto = obtener_url_base_datos()
    if not url_texto or not url_texto.startswith("postgresql"):
        pytest.fail("Las pruebas de eventos requieren DATABASE_URL de PostgreSQL.", pytrace=False)
    url = make_url(url_texto)
    nombre = f"iglesias_eventos_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    creado = False
    try:
        try:
            with admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
            creado = True
        except DBAPIError:
            pytest.fail("No se pudo crear la base temporal; revisa PostgreSQL.", pytrace=False)
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
def sesion(motor):
    """Cada prueba trabaja en una transacción que se deshace al terminar."""
    with motor.connect() as conexion:
        transaccion = conexion.begin()
        with Session(bind=conexion) as s:
            try:
                yield s
            finally:
                if transaccion.is_active:
                    transaccion.rollback()


@pytest.fixture
def mundo(sesion, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(32))
    cuarta = Iglesia(nombre="4ta IAFCJ de Mérida")
    sexta = Iglesia(nombre="6ta IAFCJ de Mérida")
    sesion.add_all([cuarta, sexta])
    sesion.flush()

    def cuenta(usuario, cargo, iglesia, activo=True):
        fila = Usuario(
            nombre_usuario=usuario,
            nombre_completo=f"Persona {usuario}",
            contrasena_hash=crear_hash(secrets.token_urlsafe(16)),
            cargo=cargo,
            iglesia_id=iglesia.id if iglesia else None,
            activo=activo,
        )
        sesion.add(fila)
        sesion.flush()
        return fila

    cuentas = {
        "presbitero": cuenta("presbitero.a", "presbitero", None),
        "pastor4": cuenta("pastor.cuarta", "pastor", cuarta),
        "apoyo4": cuenta("apoyo.cuarta", "apoyo_pastor", cuarta),
        "pastor6": cuenta("pastor.sexta", "pastor", sexta),
        "tesorero4": cuenta("tesorero.cuarta", "tesorero", cuarta),
        "lider4": cuenta("lider.cuarta", "lider_celula", cuarta),
        "baja4": cuenta("pastor.baja", "pastor", cuarta, activo=False),
    }
    return {"cuarta": cuarta, "sexta": sexta, "cuentas": cuentas}


@pytest.fixture
def cliente(sesion, mundo):
    aplicacion = crear_app()

    def sesion_prueba():
        yield sesion

    aplicacion.dependency_overrides[get_db] = sesion_prueba
    with TestClient(aplicacion) as c:
        yield c
    aplicacion.dependency_overrides.clear()


def cabecera(mundo, quien):
    return {"Authorization": f"Bearer {crear_token(str(mundo['cuentas'][quien].id))}"}


def cuerpo(fecha=MANANA, iglesia_id=None, **extra):
    return {"titulo": "Retiro de jóvenes", "fecha": fecha.isoformat(), "hora": "19:30", **extra} | {
        "iglesia_id": iglesia_id
    }


def crear_evento(cliente, mundo, quien, **kwargs):
    respuesta = cliente.post("/eventos", json=cuerpo(**kwargs), headers=cabecera(mundo, quien))
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


# ---- Sesión -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("get", "/eventos"),
        ("get", "/eventos/1"),
        ("post", "/eventos"),
        ("post", "/eventos/1/cancelar"),
    ],
)
def test_sin_sesion_da_401(cliente, metodo, ruta):
    assert getattr(cliente, metodo)(ruta).status_code == 401


def test_cuenta_desactivada_con_token_valido_da_401(cliente, mundo):
    respuesta = cliente.get("/eventos", headers=cabecera(mundo, "baja4"))
    assert respuesta.status_code == 401


# ---- Quién crea -------------------------------------------------------------------------------


def test_presbitero_crea_para_todo_el_presbiterio(cliente, mundo):
    evento = crear_evento(cliente, mundo, "presbitero", iglesia_id=None)
    assert evento["iglesia_id"] is None
    assert evento["iglesia_nombre"] is None
    assert evento["cancelado"] is False


def test_pastor_y_apoyo_crean_en_su_iglesia(cliente, mundo):
    for quien in ("pastor4", "apoyo4"):
        evento = crear_evento(cliente, mundo, quien, iglesia_id=mundo["cuarta"].id)
        assert evento["iglesia_nombre"] == "4ta IAFCJ de Mérida"


@pytest.mark.parametrize("quien", ["pastor4", "apoyo4"])
def test_pastor_y_apoyo_no_crean_para_todo_el_presbiterio(cliente, mundo, quien):
    respuesta = cliente.post(
        "/eventos", json=cuerpo(iglesia_id=None), headers=cabecera(mundo, quien)
    )
    assert respuesta.status_code == 403


def test_pastor_no_crea_en_otra_iglesia(cliente, mundo):
    respuesta = cliente.post(
        "/eventos", json=cuerpo(iglesia_id=mundo["sexta"].id), headers=cabecera(mundo, "pastor4")
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("quien", ["tesorero4", "lider4"])
def test_otros_cargos_no_crean(cliente, mundo, quien):
    respuesta = cliente.post(
        "/eventos", json=cuerpo(iglesia_id=mundo["cuarta"].id), headers=cabecera(mundo, quien)
    )
    assert respuesta.status_code == 403


def test_quien_crea_queda_registrado(cliente, mundo, sesion):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    assert sesion.get(Evento, evento["id"]).creado_por == mundo["cuentas"]["pastor4"].id


# ---- Validación -------------------------------------------------------------------------------


def test_no_se_crea_con_fecha_pasada(cliente, mundo):
    respuesta = cliente.post(
        "/eventos", json=cuerpo(fecha=AYER), headers=cabecera(mundo, "presbitero")
    )
    assert respuesta.status_code == 422


def test_se_puede_crear_para_hoy(cliente, mundo):
    assert crear_evento(cliente, mundo, "presbitero", fecha=HOY)["fecha"] == HOY.isoformat()


@pytest.mark.parametrize(
    "cambio",
    [
        {"titulo": "   "},
        {"titulo": "x" * 151},
        {"hora": "7pm"},
        {"hora": "19:30+00:00"},
        {"extra": 1},
    ],
)
def test_datos_invalidos_dan_422(cliente, mundo, cambio):
    datos = cuerpo() | cambio
    respuesta = cliente.post("/eventos", json=datos, headers=cabecera(mundo, "presbitero"))
    assert respuesta.status_code == 422


def test_iglesia_inexistente_da_422(cliente, mundo):
    respuesta = cliente.post(
        "/eventos", json=cuerpo(iglesia_id=999999), headers=cabecera(mundo, "presbitero")
    )
    assert respuesta.status_code == 422


def test_lugar_y_descripcion_vacios_quedan_nulos(cliente, mundo):
    evento = crear_evento(cliente, mundo, "presbitero", lugar="  ", descripcion="")
    assert evento["lugar"] is None
    assert evento["descripcion"] is None


# ---- Lista y detalle --------------------------------------------------------------------------


def test_cada_quien_ve_su_iglesia_y_el_presbiterio(cliente, mundo):
    general = crear_evento(cliente, mundo, "presbitero", iglesia_id=None)
    de_cuarta = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    de_sexta = crear_evento(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id)

    def ids(quien):
        return {e["id"] for e in cliente.get("/eventos", headers=cabecera(mundo, quien)).json()}

    assert ids("presbitero") == {general["id"], de_cuarta["id"], de_sexta["id"]}
    assert ids("pastor4") == {general["id"], de_cuarta["id"]}
    assert ids("lider4") == {general["id"], de_cuarta["id"]}
    assert ids("pastor6") == {general["id"], de_sexta["id"]}


def test_la_lista_va_en_orden_y_desde_hoy(cliente, mundo, sesion):
    tarde = crear_evento(cliente, mundo, "presbitero", fecha=PASADO)
    temprano = crear_evento(cliente, mundo, "presbitero", fecha=MANANA)
    sesion.add(
        Evento(
            titulo="Ya pasó",
            fecha=AYER,
            hora=sesion.get(Evento, temprano["id"]).hora,
            creado_por=mundo["cuentas"]["presbitero"].id,
        )
    )
    sesion.flush()
    ids = [e["id"] for e in cliente.get("/eventos", headers=cabecera(mundo, "presbitero")).json()]
    assert ids == [temprano["id"], tarde["id"]]
    antiguos = cliente.get(
        f"/eventos?desde={AYER.isoformat()}", headers=cabecera(mundo, "presbitero")
    ).json()
    assert len(antiguos) == 3


def test_filtro_por_iglesia_incluye_los_de_todo_el_presbiterio(cliente, mundo):
    general = crear_evento(cliente, mundo, "presbitero", iglesia_id=None)
    crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    de_sexta = crear_evento(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id)
    ruta = f"/eventos?iglesia_id={mundo['sexta'].id}"
    ids = {e["id"] for e in cliente.get(ruta, headers=cabecera(mundo, "presbitero")).json()}
    assert ids == {general["id"], de_sexta["id"]}


def test_nadie_mas_que_el_presbitero_consulta_otra_iglesia(cliente, mundo):
    ruta = f"/eventos?iglesia_id={mundo['sexta'].id}"
    assert cliente.get(ruta, headers=cabecera(mundo, "pastor4")).status_code == 403


def test_detalle_de_otra_iglesia_no_se_revela(cliente, mundo):
    de_sexta = crear_evento(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id)
    respuesta = cliente.get(f"/eventos/{de_sexta['id']}", headers=cabecera(mundo, "pastor4"))
    assert respuesta.status_code == 404
    assert (
        cliente.get(f"/eventos/{de_sexta['id']}", headers=cabecera(mundo, "presbitero")).status_code
        == 200
    )


# ---- Editar -----------------------------------------------------------------------------------


def test_pastor_edita_su_evento(cliente, mundo):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    nuevo = cuerpo(fecha=PASADO, iglesia_id=mundo["cuarta"].id, lugar="El templo") | {
        "titulo": "Retiro de damas"
    }
    respuesta = cliente.put(
        f"/eventos/{evento['id']}", json=nuevo, headers=cabecera(mundo, "apoyo4")
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["titulo"] == "Retiro de damas"
    assert respuesta.json()["lugar"] == "El templo"


def test_pastor_no_mueve_su_evento_a_otra_iglesia_ni_al_presbiterio(cliente, mundo):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    for destino in (mundo["sexta"].id, None):
        respuesta = cliente.put(
            f"/eventos/{evento['id']}",
            json=cuerpo(iglesia_id=destino),
            headers=cabecera(mundo, "pastor4"),
        )
        assert respuesta.status_code == 403


def test_pastor_no_edita_un_evento_de_todo_el_presbiterio(cliente, mundo):
    general = crear_evento(cliente, mundo, "presbitero", iglesia_id=None)
    respuesta = cliente.put(
        f"/eventos/{general['id']}",
        json=cuerpo(iglesia_id=mundo["cuarta"].id),
        headers=cabecera(mundo, "pastor4"),
    )
    assert respuesta.status_code == 403


def test_tesorero_no_edita(cliente, mundo):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    respuesta = cliente.put(
        f"/eventos/{evento['id']}",
        json=cuerpo(iglesia_id=mundo["cuarta"].id),
        headers=cabecera(mundo, "tesorero4"),
    )
    assert respuesta.status_code == 403


def test_editar_un_evento_ajeno_da_404(cliente, mundo):
    de_sexta = crear_evento(cliente, mundo, "pastor6", iglesia_id=mundo["sexta"].id)
    respuesta = cliente.put(
        f"/eventos/{de_sexta['id']}",
        json=cuerpo(iglesia_id=mundo["sexta"].id),
        headers=cabecera(mundo, "pastor4"),
    )
    assert respuesta.status_code == 404


def test_se_puede_corregir_un_evento_sin_exigir_fecha_futura(cliente, mundo, sesion):
    evento = crear_evento(cliente, mundo, "presbitero", fecha=HOY)
    sesion.get(Evento, evento["id"]).fecha = AYER
    sesion.flush()
    respuesta = cliente.put(
        f"/eventos/{evento['id']}",
        json=cuerpo(fecha=AYER) | {"titulo": "Corregido"},
        headers=cabecera(mundo, "presbitero"),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["titulo"] == "Corregido"
    assert respuesta.json()["fecha"] == AYER.isoformat()


# ---- Cancelar ---------------------------------------------------------------------------------


def test_cancelar_no_borra_y_queda_marcado(cliente, mundo, sesion):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    respuesta = cliente.post(
        f"/eventos/{evento['id']}/cancelar", headers=cabecera(mundo, "pastor4")
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["cancelado"] is True
    assert sesion.get(Evento, evento["id"]).cancelado_en is not None
    en_lista = cliente.get("/eventos", headers=cabecera(mundo, "pastor4")).json()
    assert [(e["id"], e["cancelado"]) for e in en_lista] == [(evento["id"], True)]


def test_cancelar_dos_veces_da_409_y_un_cancelado_no_se_edita(cliente, mundo):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    cliente.post(f"/eventos/{evento['id']}/cancelar", headers=cabecera(mundo, "pastor4"))
    assert (
        cliente.post(
            f"/eventos/{evento['id']}/cancelar", headers=cabecera(mundo, "pastor4")
        ).status_code
        == 409
    )
    editar = cliente.put(
        f"/eventos/{evento['id']}",
        json=cuerpo(iglesia_id=mundo["cuarta"].id),
        headers=cabecera(mundo, "pastor4"),
    )
    assert editar.status_code == 409


def test_quien_no_administra_no_cancela(cliente, mundo):
    evento = crear_evento(cliente, mundo, "pastor4", iglesia_id=mundo["cuarta"].id)
    assert (
        cliente.post(
            f"/eventos/{evento['id']}/cancelar", headers=cabecera(mundo, "lider4")
        ).status_code
        == 403
    )
    assert (
        cliente.post(
            f"/eventos/{evento['id']}/cancelar", headers=cabecera(mundo, "pastor6")
        ).status_code
        == 404
    )


def test_el_presbitero_cancela_cualquiera(cliente, mundo):
    general = crear_evento(cliente, mundo, "presbitero", iglesia_id=None)
    assert (
        cliente.post(
            f"/eventos/{general['id']}/cancelar", headers=cabecera(mundo, "presbitero")
        ).status_code
        == 200
    )
