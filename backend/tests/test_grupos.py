"""#20: grupos por alcance de cargo. Corre sobre SQLite en memoria (no necesita PostgreSQL).

Todos los datos son ficticios.
"""

import secrets
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import crear_app
from app.modelos import Grupo, GrupoMiembro, Iglesia, Miembro, Usuario
from app.modelos.listas import TIPOS_GRUPO
from app.seguridad.tokens import crear_token

TABLAS = ("iglesias", "miembros", "usuarios", "grupos", "grupo_miembros")


@dataclass
class Mundo:
    cliente: TestClient
    fabrica: sessionmaker
    iglesias: dict[str, int] = field(default_factory=dict)
    miembros: dict[str, int] = field(default_factory=dict)
    cuentas: dict[str, int] = field(default_factory=dict)
    grupos: dict[str, int] = field(default_factory=dict)

    def cab(self, clave: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {crear_token(str(self.cuentas[clave]))}"}


def sembrar(sesion) -> dict[str, dict[str, int]]:
    a = Iglesia(nombre="Iglesia ficticia A")
    b = Iglesia(nombre="Iglesia ficticia B")
    sesion.add_all([a, b])
    sesion.flush()

    def miembro(nombre, iglesia) -> Miembro:
        nuevo = Miembro(nombre=nombre, iglesia_id=iglesia.id, estado="activo")
        sesion.add(nuevo)
        sesion.flush()
        return nuevo

    jose, ana = miembro("José Pérez", a), miembro("Ana López", a)
    sofia, dani = miembro("Sofía Dirigente", a), miembro("Daniel Jóvenes", a)
    luz, carla = miembro("Luz Asistente", a), miembro("Carla Externa", b)

    celula = Grupo(iglesia_id=a.id, tipo="celula", nombre="Célula Norte", lider_miembro_id=sofia.id)
    jovenes = Grupo(
        iglesia_id=a.id,
        tipo="red",
        nombre="Jóvenes",
        lider_miembro_id=dani.id,
        asistente_miembro_id=luz.id,
    )
    ajeno = Grupo(iglesia_id=b.id, tipo="celula", nombre="Célula Sur", lider_miembro_id=carla.id)
    sesion.add_all([celula, jovenes, ajeno])
    sesion.flush()
    sesion.add_all(
        GrupoMiembro(grupo_id=celula.id, miembro_id=m.id, tipo_grupo="celula") for m in (jose, ana)
    )

    cuentas: dict[str, int] = {}

    def cuenta(clave, cargo, iglesia, ficha=None) -> None:
        nueva = Usuario(
            nombre_usuario=f"cuenta.{clave}",
            nombre_completo=f"Persona ficticia {clave}",
            contrasena_hash="hash-ficticio-no-se-usa",
            cargo=cargo,
            iglesia_id=None if iglesia is None else iglesia.id,
            activo=True,
            miembro_id=None if ficha is None else ficha.id,
        )
        sesion.add(nueva)
        sesion.flush()
        cuentas[clave] = nueva.id

    cuenta("presbitero", "presbitero", None)
    cuenta("pastor_a", "pastor", a)
    cuenta("apoyo_a", "apoyo_pastor", a)
    cuenta("tesorero_a", "tesorero", a)
    cuenta("lider_celula_a", "lider_celula", a, sofia)
    cuenta("lider_red_a", "lider_red", a, dani)
    cuenta("diacono_a", "diacono", a)
    cuenta("pastor_b", "pastor", b)
    sesion.commit()
    return {
        "iglesias": {"a": a.id, "b": b.id},
        "miembros": {
            "jose": jose.id,
            "ana": ana.id,
            "sofia": sofia.id,
            "dani": dani.id,
            "luz": luz.id,
            "carla": carla.id,
        },
        "cuentas": cuentas,
        "grupos": {"celula": celula.id, "jovenes": jovenes.id, "ajeno": ajeno.id},
    }


@pytest.fixture
def mundo(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(32))
    motor = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )

    @event.listens_for(motor, "connect")
    def activar_llaves(conexion, _):
        conexion.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(motor, tables=[Base.metadata.tables[n] for n in TABLAS])
    fabrica = sessionmaker(bind=motor)
    with fabrica() as sesion:
        datos = sembrar(sesion)
    aplicacion = crear_app()

    def sesion_prueba():
        with fabrica() as sesion:
            yield sesion

    aplicacion.dependency_overrides[get_db] = sesion_prueba
    try:
        with TestClient(aplicacion) as cliente:
            yield Mundo(cliente=cliente, fabrica=fabrica, **datos)
    finally:
        aplicacion.dependency_overrides.clear()
        motor.dispose()


def nombres(respuesta) -> list[str]:
    assert respuesta.status_code == 200, respuesta.text
    return [g["nombre"] for g in respuesta.json()]


def grupo(mundo: Mundo, **cambios) -> dict:
    base = {
        "nombre": "Grupo ficticio",
        "tipo": "ministerio",
        "iglesia_id": mundo.iglesias["a"],
        "lider_id": mundo.miembros["jose"],
        "asistente_id": mundo.miembros["ana"],
    }
    return {**base, **cambios}


# ---- Quién ve qué grupos ----


def test_sin_sesion_no_ve_grupos(mundo):
    assert mundo.cliente.get("/grupos").status_code == 401


def test_presbitero_ve_todos_los_grupos(mundo):
    r = mundo.cliente.get("/grupos", headers=mundo.cab("presbitero"))
    assert nombres(r) == ["Célula Norte", "Célula Sur", "Jóvenes"]


@pytest.mark.parametrize("clave", ["pastor_a", "apoyo_a"])
def test_pastor_y_apoyo_ven_los_de_su_iglesia(mundo, clave):
    r = mundo.cliente.get("/grupos", headers=mundo.cab(clave))
    assert nombres(r) == ["Célula Norte", "Jóvenes"]
    asignados = {g["nombre"]: g for g in r.json()}["Jóvenes"]
    assert asignados["lider_nombre"] == "Daniel Jóvenes"
    assert asignados["asistente_nombre"] == "Luz Asistente"
    assert asignados["iglesia_nombre"] == "Iglesia ficticia A"


def test_el_pastor_de_otra_iglesia_solo_ve_los_suyos(mundo):
    r = mundo.cliente.get("/grupos", headers=mundo.cab("pastor_b"))
    assert nombres(r) == ["Célula Sur"]


def test_cada_lider_solo_ve_su_grupo(mundo):
    assert nombres(mundo.cliente.get("/grupos", headers=mundo.cab("lider_celula_a"))) == [
        "Célula Norte"
    ]
    assert nombres(mundo.cliente.get("/grupos", headers=mundo.cab("lider_red_a"))) == ["Jóvenes"]


def test_quien_no_dirige_grupos_no_ve_ninguno(mundo):
    assert nombres(mundo.cliente.get("/grupos", headers=mundo.cab("diacono_a"))) == []


def test_el_tesorero_no_tiene_grupos_a_su_cargo(mundo):
    assert mundo.cliente.get("/grupos", headers=mundo.cab("tesorero_a")).status_code == 403


def test_un_grupo_inactivo_no_aparece(mundo):
    with mundo.fabrica() as sesion:
        sesion.get(Grupo, mundo.grupos["jovenes"]).activo = False
        sesion.commit()
    assert nombres(mundo.cliente.get("/grupos", headers=mundo.cab("pastor_a"))) == ["Célula Norte"]


def test_filtra_por_tipo(mundo):
    cab = mundo.cab("presbitero")
    assert nombres(mundo.cliente.get("/grupos?tipo=red", headers=cab)) == ["Jóvenes"]
    assert nombres(mundo.cliente.get("/grupos?tipo=celula", headers=cab)) == [
        "Célula Norte",
        "Célula Sur",
    ]
    assert mundo.cliente.get("/grupos?tipo=club", headers=cab).status_code == 422


# ---- Detalle ----


def test_detalle_con_los_ids_de_lider_y_asistente(mundo):
    r = mundo.cliente.get(f"/grupos/{mundo.grupos['jovenes']}", headers=mundo.cab("pastor_a"))
    assert r.status_code == 200
    assert r.json() == {
        "id": mundo.grupos["jovenes"],
        "nombre": "Jóvenes",
        "tipo": "red",
        "iglesia_id": mundo.iglesias["a"],
        "lider_id": mundo.miembros["dani"],
        "asistente_id": mundo.miembros["luz"],
    }


def test_un_grupo_fuera_del_alcance_se_ve_como_inexistente(mundo):
    ajeno = mundo.grupos["ajeno"]
    assert mundo.cliente.get(f"/grupos/{ajeno}", headers=mundo.cab("pastor_a")).status_code == 404
    assert mundo.cliente.get(f"/grupos/{ajeno}", headers=mundo.cab("presbitero")).status_code == 200
    # Un líder no abre el grupo de otro líder.
    otro = mundo.grupos["jovenes"]
    assert (
        mundo.cliente.get(f"/grupos/{otro}", headers=mundo.cab("lider_celula_a")).status_code == 404
    )
    assert mundo.cliente.get("/grupos/99999", headers=mundo.cab("presbitero")).status_code == 404


# ---- Alta ----


@pytest.mark.parametrize("clave", ["presbitero", "pastor_a", "apoyo_a"])
def test_presbitero_pastor_y_apoyo_crean_grupos(mundo, clave):
    r = mundo.cliente.post("/grupos", json=grupo(mundo), headers=mundo.cab(clave))
    assert r.status_code == 201, r.text
    with mundo.fabrica() as sesion:
        creado = sesion.get(Grupo, r.json()["id"])
        assert creado.lider_miembro_id == mundo.miembros["jose"]
        assert creado.asistente_miembro_id == mundo.miembros["ana"]
        assert creado.activo is True


@pytest.mark.parametrize("tipo", TIPOS_GRUPO)
def test_acepta_los_cinco_tipos(mundo, tipo):
    r = mundo.cliente.post("/grupos", json=grupo(mundo, tipo=tipo), headers=mundo.cab("pastor_a"))
    assert r.status_code == 201


@pytest.mark.parametrize("clave", ["tesorero_a", "lider_celula_a", "lider_red_a", "diacono_a"])
def test_otros_cargos_no_crean_grupos(mundo, clave):
    r = mundo.cliente.post("/grupos", json=grupo(mundo), headers=mundo.cab(clave))
    assert r.status_code == 403


def test_el_pastor_no_crea_grupos_en_otra_iglesia(mundo):
    datos = grupo(
        mundo,
        iglesia_id=mundo.iglesias["b"],
        lider_id=mundo.miembros["carla"],
        asistente_id=None,
    )
    assert (
        mundo.cliente.post("/grupos", json=datos, headers=mundo.cab("pastor_a")).status_code == 403
    )
    assert (
        mundo.cliente.post("/grupos", json=datos, headers=mundo.cab("presbitero")).status_code
        == 201
    )


def test_el_asistente_es_opcional(mundo):
    r = mundo.cliente.post(
        "/grupos", json=grupo(mundo, asistente_id=None), headers=mundo.cab("pastor_a")
    )
    assert r.status_code == 201
    assert r.json()["asistente_id"] is None


@pytest.mark.parametrize(
    "cambio",
    [
        {"nombre": ""},
        {"nombre": "   "},
        {"tipo": "club"},
        {"tipo": None},
        {"iglesia_id": 0},
        {"iglesia_id": 99999},
        {"lider_id": 0},
        {"lider_id": 99999},
        {"asistente_id": 99999},
    ],
)
def test_rechaza_datos_no_validos(mundo, cambio):
    r = mundo.cliente.post("/grupos", json=grupo(mundo, **cambio), headers=mundo.cab("presbitero"))
    assert r.status_code == 422


def test_el_lider_y_el_asistente_deben_ser_de_la_iglesia_del_grupo(mundo):
    cab = mundo.cab("presbitero")
    de_otra = mundo.miembros["carla"]
    assert (
        mundo.cliente.post("/grupos", json=grupo(mundo, lider_id=de_otra), headers=cab).status_code
        == 422
    )
    assert (
        mundo.cliente.post(
            "/grupos", json=grupo(mundo, asistente_id=de_otra), headers=cab
        ).status_code
        == 422
    )


def test_el_asistente_no_puede_ser_el_lider(mundo):
    jose = mundo.miembros["jose"]
    r = mundo.cliente.post(
        "/grupos",
        json=grupo(mundo, lider_id=jose, asistente_id=jose),
        headers=mundo.cab("pastor_a"),
    )
    assert r.status_code == 422


def test_no_repite_el_nombre_en_la_misma_iglesia_y_tipo(mundo):
    cab = mundo.cab("pastor_a")
    assert (
        mundo.cliente.post("/grupos", json=grupo(mundo, nombre="Alabanza"), headers=cab).status_code
        == 201
    )
    assert (
        mundo.cliente.post("/grupos", json=grupo(mundo, nombre="Alabanza"), headers=cab).status_code
        == 409
    )
    # Con otro tipo, o en otra iglesia, el mismo nombre sí se puede.
    otro_tipo = grupo(mundo, nombre="Alabanza", tipo="area")
    assert mundo.cliente.post("/grupos", json=otro_tipo, headers=cab).status_code == 201
    otra_iglesia = grupo(
        mundo,
        nombre="Alabanza",
        iglesia_id=mundo.iglesias["b"],
        lider_id=mundo.miembros["carla"],
        asistente_id=None,
    )
    assert (
        mundo.cliente.post(
            "/grupos", json=otra_iglesia, headers=mundo.cab("presbitero")
        ).status_code
        == 201
    )


def test_no_se_aceptan_campos_desconocidos_y_el_error_no_repite_lo_enviado(mundo):
    r = mundo.cliente.post(
        "/grupos",
        json={**grupo(mundo, nombre="   "), "secreto": "valor-privado"},
        headers=mundo.cab("pastor_a"),
    )
    assert r.status_code == 422
    assert "valor-privado" not in r.text


# ---- Edición ----


def test_el_pastor_edita_el_nombre_el_lider_y_el_asistente(mundo):
    destino = mundo.grupos["jovenes"]
    datos = grupo(
        mundo,
        nombre="Jóvenes Unidos",
        tipo="red",
        lider_id=mundo.miembros["jose"],
        asistente_id=None,
    )
    r = mundo.cliente.put(f"/grupos/{destino}", json=datos, headers=mundo.cab("pastor_a"))
    assert r.status_code == 200, r.text
    with mundo.fabrica() as sesion:
        editado = sesion.get(Grupo, destino)
        assert editado.nombre == "Jóvenes Unidos"
        assert editado.lider_miembro_id == mundo.miembros["jose"]
        assert editado.asistente_miembro_id is None


def test_no_edita_grupos_de_otra_iglesia(mundo):
    r = mundo.cliente.put(
        f"/grupos/{mundo.grupos['ajeno']}", json=grupo(mundo), headers=mundo.cab("pastor_a")
    )
    assert r.status_code == 404


def test_el_lider_administra_solo_su_grupo_nombre_y_asistente(mundo):
    """Criterio del #20: un líder solo administra su grupo."""
    celula = mundo.grupos["celula"]
    cab = mundo.cab("lider_celula_a")
    datos = grupo(
        mundo,
        nombre="Célula Norte Renovada",
        tipo="celula",
        lider_id=mundo.miembros["sofia"],
        asistente_id=mundo.miembros["ana"],
    )
    r = mundo.cliente.put(f"/grupos/{celula}", json=datos, headers=cab)
    assert r.status_code == 200, r.text
    assert r.json()["nombre"] == "Célula Norte Renovada"
    assert r.json()["asistente_id"] == mundo.miembros["ana"]


@pytest.mark.parametrize(
    "cambio",
    [
        {"lider_id": "jose"},
        {"tipo": "ministerio"},
        {"iglesia_id": "b"},
    ],
)
def test_el_lider_no_cambia_lider_tipo_ni_iglesia(mundo, cambio):
    celula = mundo.grupos["celula"]
    datos = grupo(
        mundo,
        nombre="Célula Norte",
        tipo="celula",
        lider_id=mundo.miembros["sofia"],
        asistente_id=None,
    )
    for campo, valor in cambio.items():
        if campo == "lider_id":
            datos[campo] = mundo.miembros[valor]
        elif campo == "iglesia_id":
            datos[campo] = mundo.iglesias[valor]
        else:
            datos[campo] = valor
    r = mundo.cliente.put(f"/grupos/{celula}", json=datos, headers=mundo.cab("lider_celula_a"))
    assert r.status_code == 403
    with mundo.fabrica() as sesion:
        assert sesion.get(Grupo, celula).lider_miembro_id == mundo.miembros["sofia"]


def test_un_lider_no_edita_el_grupo_de_otro(mundo):
    r = mundo.cliente.put(
        f"/grupos/{mundo.grupos['jovenes']}", json=grupo(mundo), headers=mundo.cab("lider_celula_a")
    )
    assert r.status_code == 404


@pytest.mark.parametrize("clave", ["tesorero_a", "diacono_a"])
def test_otros_cargos_no_editan_grupos(mundo, clave):
    r = mundo.cliente.put(
        f"/grupos/{mundo.grupos['celula']}", json=grupo(mundo), headers=mundo.cab(clave)
    )
    assert r.status_code in {403, 404}


def test_no_cambia_el_tipo_de_un_grupo_con_integrantes_pero_si_sin_ellos(mundo):
    cab = mundo.cab("pastor_a")
    con_integrantes = grupo(
        mundo, nombre="Célula Norte", tipo="ministerio", lider_id=mundo.miembros["sofia"]
    )
    r = mundo.cliente.put(f"/grupos/{mundo.grupos['celula']}", json=con_integrantes, headers=cab)
    assert r.status_code == 409
    sin_integrantes = grupo(
        mundo, nombre="Jóvenes", tipo="escuela", lider_id=mundo.miembros["dani"]
    )
    r = mundo.cliente.put(f"/grupos/{mundo.grupos['jovenes']}", json=sin_integrantes, headers=cab)
    assert r.status_code == 200
    assert r.json()["tipo"] == "escuela"


def test_renombrar_no_choca_con_el_propio_nombre_pero_si_con_otro_grupo(mundo):
    cab = mundo.cab("pastor_a")
    propio = grupo(mundo, nombre="Jóvenes", tipo="red", lider_id=mundo.miembros["dani"])
    assert (
        mundo.cliente.put(
            f"/grupos/{mundo.grupos['jovenes']}", json=propio, headers=cab
        ).status_code
        == 200
    )
    otro = mundo.cliente.post(
        "/grupos", json=grupo(mundo, nombre="Hombres", tipo="red"), headers=cab
    )
    assert otro.status_code == 201
    choque = grupo(mundo, nombre="Jóvenes", tipo="red", lider_id=mundo.miembros["jose"])
    assert (
        mundo.cliente.put(f"/grupos/{otro.json()['id']}", json=choque, headers=cab).status_code
        == 409
    )
