"""#17: miembros por alcance de cargo. Corre sobre SQLite en memoria (no necesita PostgreSQL).

Los datos son ficticios. El armado `mundo` también lo reutilizan las pruebas de grupos y asistencia.
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
from app.modelos.listas import ESTADOS_MIEMBRO
from app.seguridad.tokens import crear_token

TABLAS = ("iglesias", "miembros", "usuarios", "grupos", "grupo_miembros", "asistencias")


@dataclass
class Mundo:
    cliente: TestClient
    fabrica: sessionmaker
    iglesias: dict[str, int] = field(default_factory=dict)
    miembros: dict[str, int] = field(default_factory=dict)
    cuentas: dict[str, int] = field(default_factory=dict)
    grupos: dict[str, int] = field(default_factory=dict)

    def cab(self, clave: str) -> dict[str, str]:
        """Cabecera de sesión de la cuenta `clave`."""
        return {"Authorization": f"Bearer {crear_token(str(self.cuentas[clave]))}"}


def sembrar(sesion) -> dict[str, dict[str, int]]:
    a = Iglesia(nombre="Iglesia ficticia A")
    b = Iglesia(nombre="Iglesia ficticia B")
    sesion.add_all([a, b])
    sesion.flush()

    def miembro(nombre, iglesia, estado="activo", **extra) -> Miembro:
        nuevo = Miembro(nombre=nombre, iglesia_id=iglesia.id, estado=estado, **extra)
        sesion.add(nuevo)
        sesion.flush()
        return nuevo

    jose = miembro("José Pérez", a, telefono="999 000 0001")
    ana = miembro("Ana López", a, estado="visitante")
    luis = miembro("Luis Ñandú", a, estado="inactivo")
    sofia = miembro("Sofía Dirigente", a)
    carla = miembro("Carla Externa", b)

    celula = Grupo(
        iglesia_id=a.id, tipo="celula", nombre="Célula Norte", lider_miembro_id=sofia.id
    )
    sesion.add(celula)
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
    cuenta("lider_a", "lider_celula", a, sofia)
    cuenta("diacono_a", "diacono", a)
    cuenta("ujier_a", "ujier", a)
    cuenta("pastor_b", "pastor", b)
    sesion.commit()
    return {
        "iglesias": {"a": a.id, "b": b.id},
        "miembros": {
            "jose": jose.id,
            "ana": ana.id,
            "luis": luis.id,
            "sofia": sofia.id,
            "carla": carla.id,
        },
        "cuentas": cuentas,
        "grupos": {"celula": celula.id},
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
    return [m["nombre"] for m in respuesta.json()]


NUEVO = {
    "nombre": "Pedro Ficticio",
    "telefono": "999 000 0099",
    "correo": "pedro@ejemplo.com",
    "fecha_nacimiento": "1990-05-01",
    "direccion": "Calle ficticia 1",
    "estado_civil": "casado",
    "fecha_bautizo": "2010-01-10",
    "fecha_ingreso": "2009-03-01",
    "estado": "activo",
}


def nuevo(mundo: Mundo, iglesia: str = "a", **cambios) -> dict:
    return {**NUEVO, "iglesia_id": mundo.iglesias[iglesia], **cambios}


# ---- Quién ve a quién ----


def test_sin_sesion_no_ve_miembros(mundo):
    assert mundo.cliente.get("/miembros").status_code == 401


def test_presbitero_ve_todo_el_presbiterio(mundo):
    r = mundo.cliente.get("/miembros", headers=mundo.cab("presbitero"))
    assert nombres(r) == [
        "Ana López",
        "Carla Externa",
        "José Pérez",
        "Luis Ñandú",
        "Sofía Dirigente",
    ]
    assert {m["iglesia_nombre"] for m in r.json()} == {"Iglesia ficticia A", "Iglesia ficticia B"}


@pytest.mark.parametrize("clave", ["pastor_a", "apoyo_a"])
def test_pastor_y_apoyo_ven_solo_su_iglesia(mundo, clave):
    r = mundo.cliente.get("/miembros", headers=mundo.cab(clave))
    assert nombres(r) == ["Ana López", "José Pérez", "Luis Ñandú", "Sofía Dirigente"]


def test_pastor_de_otra_iglesia_solo_ve_la_suya(mundo):
    r = mundo.cliente.get("/miembros", headers=mundo.cab("pastor_b"))
    assert nombres(r) == ["Carla Externa"]


def test_el_tesorero_no_ve_la_lista_de_miembros(mundo):
    """D20, regla 3."""
    cab = mundo.cab("tesorero_a")
    assert mundo.cliente.get("/miembros", headers=cab).status_code == 403
    assert mundo.cliente.post("/miembros/buscar", json={}, headers=cab).status_code == 403
    assert (
        mundo.cliente.get(f"/miembros/{mundo.miembros['jose']}", headers=cab).status_code == 403
    )


def test_un_lider_solo_ve_a_los_integrantes_de_su_grupo(mundo):
    """D21: el área de un líder son los grupos que dirige su ficha de miembro."""
    r = mundo.cliente.get("/miembros", headers=mundo.cab("lider_a"))
    assert nombres(r) == ["Ana López", "José Pérez"]


@pytest.mark.parametrize("clave", ["diacono_a", "ujier_a"])
def test_cargo_sin_grupos_ni_ficha_no_ve_a_nadie(mundo, clave):
    assert nombres(mundo.cliente.get("/miembros", headers=mundo.cab(clave))) == []


def test_un_grupo_inactivo_ya_no_concede_acceso(mundo):
    with mundo.fabrica() as sesion:
        sesion.get(Grupo, mundo.grupos["celula"]).activo = False
        sesion.commit()
    assert nombres(mundo.cliente.get("/miembros", headers=mundo.cab("lider_a"))) == []


def test_filtra_por_estado_y_por_iglesia(mundo):
    cab = mundo.cab("presbitero")
    assert nombres(mundo.cliente.get("/miembros?estado=visitante", headers=cab)) == ["Ana López"]
    r = mundo.cliente.get(f"/miembros?iglesia_id={mundo.iglesias['b']}", headers=cab)
    assert nombres(r) == ["Carla Externa"]
    assert mundo.cliente.get("/miembros?estado=raro", headers=cab).status_code == 422


# ---- Búsqueda por nombre (en el cuerpo, no en la dirección) ----


def test_busca_por_nombre_sin_importar_acentos_ni_mayusculas(mundo):
    cab = mundo.cab("pastor_a")

    def buscar(texto: str) -> list[str]:
        return nombres(mundo.cliente.post("/miembros/buscar", json={"texto": texto}, headers=cab))

    assert buscar("jose") == ["José Pérez"]
    assert buscar("NANDU") == ["Luis Ñandú"]
    assert buscar("zzz") == []


def test_buscar_respeta_el_alcance_y_los_filtros(mundo):
    r = mundo.cliente.post("/miembros/buscar", json={"texto": "a"}, headers=mundo.cab("pastor_b"))
    assert nombres(r) == ["Carla Externa"]
    cab = mundo.cab("presbitero")
    r = mundo.cliente.post("/miembros/buscar", json={"estado": "inactivo"}, headers=cab)
    assert nombres(r) == ["Luis Ñandú"]
    r = mundo.cliente.post("/miembros/buscar", json={"estado": "raro"}, headers=cab)
    assert r.status_code == 422


def test_la_busqueda_no_pone_nombres_en_la_direccion(mundo):
    cab = mundo.cab("pastor_a")
    r = mundo.cliente.post("/miembros/buscar", json={"texto": "José"}, headers=cab)
    assert r.status_code == 200
    assert "Jos" not in str(r.request.url)


# ---- Detalle ----


def test_detalle_dentro_del_alcance(mundo):
    r = mundo.cliente.get(f"/miembros/{mundo.miembros['jose']}", headers=mundo.cab("pastor_a"))
    assert r.status_code == 200
    assert r.json()["nombre"] == "José Pérez"
    assert set(r.json()) == {
        "id",
        "nombre",
        "telefono",
        "correo",
        "fecha_nacimiento",
        "direccion",
        "estado_civil",
        "fecha_bautizo",
        "fecha_ingreso",
        "iglesia_id",
        "estado",
    }


def test_un_miembro_fuera_del_alcance_se_ve_como_inexistente(mundo):
    carla = mundo.miembros["carla"]
    pastor, presbitero = mundo.cab("pastor_a"), mundo.cab("presbitero")
    assert mundo.cliente.get(f"/miembros/{carla}", headers=pastor).status_code == 404
    assert mundo.cliente.get(f"/miembros/{carla}", headers=presbitero).status_code == 200
    assert mundo.cliente.get("/miembros/99999", headers=presbitero).status_code == 404
    # El líder solo abre a quienes están en su grupo.
    luis = mundo.miembros["luis"]
    assert mundo.cliente.get(f"/miembros/{luis}", headers=mundo.cab("lider_a")).status_code == 404


# ---- Alta ----


@pytest.mark.parametrize("clave", ["presbitero", "pastor_a", "apoyo_a"])
def test_presbitero_pastor_y_apoyo_registran_miembros(mundo, clave):
    r = mundo.cliente.post("/miembros", json=nuevo(mundo), headers=mundo.cab(clave))
    assert r.status_code == 201, r.text
    assert r.json()["nombre"] == "Pedro Ficticio"
    assert r.json()["iglesia_id"] == mundo.iglesias["a"]
    with mundo.fabrica() as sesion:
        assert sesion.get(Miembro, r.json()["id"]).correo == "pedro@ejemplo.com"


@pytest.mark.parametrize("clave", ["tesorero_a", "lider_a", "diacono_a", "ujier_a"])
def test_otros_cargos_no_registran_miembros(mundo, clave):
    r = mundo.cliente.post("/miembros", json=nuevo(mundo), headers=mundo.cab(clave))
    assert r.status_code == 403


def test_el_pastor_no_registra_en_otra_iglesia_pero_el_presbitero_si(mundo):
    r = mundo.cliente.post("/miembros", json=nuevo(mundo, "b"), headers=mundo.cab("pastor_a"))
    assert r.status_code == 403
    r = mundo.cliente.post("/miembros", json=nuevo(mundo, "b"), headers=mundo.cab("presbitero"))
    assert r.status_code == 201


def test_la_iglesia_debe_existir(mundo):
    datos = {**NUEVO, "iglesia_id": 99999}
    r = mundo.cliente.post("/miembros", json=datos, headers=mundo.cab("presbitero"))
    assert r.status_code == 422


@pytest.mark.parametrize("estado", ESTADOS_MIEMBRO)
def test_acepta_los_seis_estados(mundo, estado):
    r = mundo.cliente.post(
        "/miembros", json=nuevo(mundo, estado=estado), headers=mundo.cab("pastor_a")
    )
    assert r.status_code == 201


def test_solo_el_nombre_y_la_iglesia_son_obligatorios(mundo):
    datos = {"nombre": "  Mínimo  ", "iglesia_id": mundo.iglesias["a"], "estado": "visitante"}
    r = mundo.cliente.post("/miembros", json=datos, headers=mundo.cab("pastor_a"))
    assert r.status_code == 201
    assert r.json()["nombre"] == "Mínimo"
    assert r.json()["telefono"] is None and r.json()["correo"] is None


def test_los_textos_vacios_se_guardan_como_sin_dato(mundo):
    datos = nuevo(mundo, telefono="  ", correo="", direccion=" ", estado_civil="")
    r = mundo.cliente.post("/miembros", json=datos, headers=mundo.cab("pastor_a"))
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["telefono"] is None
    assert cuerpo["correo"] is None
    assert cuerpo["direccion"] is None
    assert cuerpo["estado_civil"] is None


def test_no_se_guardan_datos_de_familia(mundo):
    """D14: se guardan todos los datos menos la familia."""
    for campo in ("familiares", "esposa", "hijos", "tutor"):
        r = mundo.cliente.post(
            "/miembros", json={**nuevo(mundo), campo: "x"}, headers=mundo.cab("pastor_a")
        )
        assert r.status_code == 422, campo


@pytest.mark.parametrize(
    "cambio",
    [
        {"nombre": ""},
        {"nombre": "   "},
        {"estado": "casi_activo"},
        {"estado": None},
        {"estado_civil": "complicado"},
        {"correo": "no-es-un-correo"},
        {"telefono": "9" * 21},
        {"fecha_nacimiento": "ayer"},
        {"iglesia_id": 0},
    ],
)
def test_rechaza_datos_no_validos(mundo, cambio):
    r = mundo.cliente.post("/miembros", json=nuevo(mundo, **cambio), headers=mundo.cab("pastor_a"))
    assert r.status_code == 422


def test_el_error_no_repite_lo_que_se_envio(mundo):
    r = mundo.cliente.post(
        "/miembros",
        json=nuevo(mundo, correo="dato-privado-no-valido"),
        headers=mundo.cab("pastor_a"),
    )
    assert r.status_code == 422
    assert "dato-privado" not in r.text
    assert "correo" in r.text


# ---- Edición ----


def test_el_pastor_edita_a_un_miembro_de_su_iglesia(mundo):
    jose = mundo.miembros["jose"]
    datos = nuevo(mundo, nombre="José Pérez Editado", estado="inactivo")
    r = mundo.cliente.put(f"/miembros/{jose}", json=datos, headers=mundo.cab("pastor_a"))
    assert r.status_code == 200
    assert r.json()["nombre"] == "José Pérez Editado"
    with mundo.fabrica() as sesion:
        assert sesion.get(Miembro, jose).estado == "inactivo"


def test_no_edita_a_quien_esta_fuera_de_su_alcance(mundo):
    carla = mundo.miembros["carla"]
    r = mundo.cliente.put(f"/miembros/{carla}", json=nuevo(mundo), headers=mundo.cab("pastor_a"))
    assert r.status_code == 404


@pytest.mark.parametrize("clave", ["tesorero_a", "lider_a", "diacono_a"])
def test_solo_los_gestores_editan(mundo, clave):
    jose = mundo.miembros["jose"]
    r = mundo.cliente.put(f"/miembros/{jose}", json=nuevo(mundo), headers=mundo.cab(clave))
    assert r.status_code == 403


def test_el_pastor_no_pasa_a_un_miembro_a_otra_iglesia(mundo):
    luis = mundo.miembros["luis"]
    r = mundo.cliente.put(
        f"/miembros/{luis}", json=nuevo(mundo, "b"), headers=mundo.cab("pastor_a")
    )
    assert r.status_code == 403


def test_el_presbitero_cambia_de_iglesia_a_quien_no_esta_en_grupos(mundo):
    luis = mundo.miembros["luis"]
    r = mundo.cliente.put(
        f"/miembros/{luis}", json=nuevo(mundo, "b"), headers=mundo.cab("presbitero")
    )
    assert r.status_code == 200
    assert r.json()["iglesia_id"] == mundo.iglesias["b"]


@pytest.mark.parametrize("miembro", ["jose", "sofia"])
def test_no_cambia_de_iglesia_quien_esta_en_grupos_o_dirige_uno(mundo, miembro):
    """José está en una célula y Sofía la dirige (y tiene cuenta ligada)."""
    r = mundo.cliente.put(
        f"/miembros/{mundo.miembros[miembro]}",
        json=nuevo(mundo, "b"),
        headers=mundo.cab("presbitero"),
    )
    assert r.status_code == 409
    with mundo.fabrica() as sesion:
        assert sesion.get(Miembro, mundo.miembros[miembro]).iglesia_id == mundo.iglesias["a"]
