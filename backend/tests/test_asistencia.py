"""#23: asistencia del líder de célula y del ujier. Corre sobre SQLite en memoria.

Todos los datos son ficticios.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import crear_app
from app.modelos import Asistencia, Grupo, GrupoMiembro, Iglesia, Miembro, Usuario
from app.modelos.listas import TIPOS_SERVICIO_ASISTENCIA
from app.seguridad.tokens import crear_token

TABLAS = ("iglesias", "miembros", "usuarios", "grupos", "grupo_miembros", "asistencias")
HOY = datetime.now(timezone.utc).date()
AYER = HOY - timedelta(days=1)


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

    def ids(self, *claves: str) -> list[int]:
        return [self.miembros[c] for c in claves]


def sembrar(sesion) -> dict[str, dict[str, int]]:
    a = Iglesia(nombre="Iglesia ficticia A")
    b = Iglesia(nombre="Iglesia ficticia B")
    sesion.add_all([a, b])
    sesion.flush()

    def miembro(nombre, iglesia, estado="activo") -> Miembro:
        nuevo = Miembro(nombre=nombre, iglesia_id=iglesia.id, estado=estado)
        sesion.add(nuevo)
        sesion.flush()
        return nuevo

    jose, ana, rut = miembro("José Pérez", a), miembro("Ana López", a), miembro("Rut Norte", a)
    tomas = miembro("Tomás Oeste", a)
    luis = miembro("Luis Ñandú", a, estado="inactivo")
    mario, eva = miembro("Mario Libre", a), miembro("Eva Visitante", a, estado="visitante")
    sofia, pedro, dani = (
        miembro("Sofía Dirigente", a),
        miembro("Pedro Otro Líder", a),
        miembro("Daniel Jóvenes", a),
    )
    carla = miembro("Carla Externa", b)

    def grupo(iglesia, tipo, nombre, lider) -> Grupo:
        nuevo = Grupo(iglesia_id=iglesia.id, tipo=tipo, nombre=nombre, lider_miembro_id=lider.id)
        sesion.add(nuevo)
        sesion.flush()
        return nuevo

    norte = grupo(a, "celula", "Célula Norte", sofia)
    este = grupo(a, "celula", "Célula Este", sofia)
    oeste = grupo(a, "celula", "Célula Oeste", pedro)
    jovenes = grupo(a, "red", "Jóvenes", dani)
    sesion.add_all(
        [
            GrupoMiembro(grupo_id=norte.id, miembro_id=jose.id, tipo_grupo="celula"),
            GrupoMiembro(grupo_id=norte.id, miembro_id=ana.id, tipo_grupo="celula"),
            GrupoMiembro(grupo_id=este.id, miembro_id=rut.id, tipo_grupo="celula"),
            GrupoMiembro(grupo_id=oeste.id, miembro_id=tomas.id, tipo_grupo="celula"),
            # Estar en una red no cuenta como tener célula.
            GrupoMiembro(grupo_id=jovenes.id, miembro_id=mario.id, tipo_grupo="red"),
        ]
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
    cuenta("tesorero_a", "tesorero", a)
    cuenta("lider_a", "lider_celula", a, sofia)
    cuenta("lider_otro_a", "lider_celula", a, pedro)
    cuenta("lider_red_a", "lider_red", a, dani)
    cuenta("lider_sin_ficha", "lider_celula", a)
    cuenta("ujier_a", "ujier", a)
    cuenta("ujier_b", "ujier", b)
    sesion.commit()
    return {
        "iglesias": {"a": a.id, "b": b.id},
        "miembros": {
            "jose": jose.id,
            "ana": ana.id,
            "rut": rut.id,
            "tomas": tomas.id,
            "luis": luis.id,
            "mario": mario.id,
            "eva": eva.id,
            "sofia": sofia.id,
            "carla": carla.id,
        },
        "cuentas": cuentas,
        "grupos": {"norte": norte.id, "este": este.id, "oeste": oeste.id},
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


def pedir(mundo, clave, fecha=HOY, servicio="culto_domingo"):
    return mundo.cliente.get(
        f"/asistencia?fecha={fecha}&servicio={servicio}", headers=mundo.cab(clave)
    )


def guardar(mundo, clave, hoja, marcados, fecha=HOY, servicio="culto_domingo"):
    cuerpo = {"fecha": str(fecha), "servicio": servicio, "hoja": hoja, "marcados": marcados}
    return mundo.cliente.put("/asistencia", json=cuerpo, headers=mundo.cab(clave))


def hojas(respuesta) -> dict[str, dict]:
    assert respuesta.status_code == 200, respuesta.text
    return {h["hoja"]: h for h in respuesta.json()}


def marcados(hoja: dict) -> list[str]:
    return sorted(p["nombre"] for p in hoja["personas"] if p["marcado"])


def filas(mundo) -> int:
    with mundo.fabrica() as sesion:
        return sesion.scalar(select(func.count()).select_from(Asistencia))


# ---- Qué hojas tiene cada cargo ----


def test_sin_sesion_no_ve_hojas(mundo):
    assert mundo.cliente.get(f"/asistencia?fecha={HOY}&servicio=culto_domingo").status_code == 401


def test_el_lider_ve_una_hoja_por_cada_celula_que_dirige(mundo):
    r = pedir(mundo, "lider_a")
    por_id = hojas(r)
    norte, este = mundo.grupos["norte"], mundo.grupos["este"]
    assert list(por_id) == [f"celula:{este}", f"celula:{norte}"]
    hoja = por_id[f"celula:{norte}"]
    assert hoja["modo"] == "asistencias"
    assert hoja["titulo"] == "Célula Norte"
    assert hoja["guardada"] is False
    assert [p["nombre"] for p in hoja["personas"]] == ["Ana López", "José Pérez"]
    assert not any(p["marcado"] for p in hoja["personas"])


def test_cada_lider_solo_ve_sus_celulas(mundo):
    por_id = hojas(pedir(mundo, "lider_otro_a"))
    assert list(por_id) == [f"celula:{mundo.grupos['oeste']}"]
    assert [p["nombre"] for p in por_id[f"celula:{mundo.grupos['oeste']}"]["personas"]] == [
        "Tomás Oeste"
    ]


def test_el_ujier_ve_a_quienes_no_tienen_celula_en_su_iglesia(mundo):
    por_id = hojas(pedir(mundo, "ujier_a"))
    assert list(por_id) == [f"sin_celula:{mundo.iglesias['a']}"]
    hoja = por_id[f"sin_celula:{mundo.iglesias['a']}"]
    assert hoja["modo"] == "faltas"
    assert hoja["titulo"] == "Sin célula"
    # Sin José, Ana, Rut ni Tomás (integrantes de una célula), sin Luis (inactivo) y sin Carla
    # (otra iglesia). Mario solo está en una red, y eso no es tener célula. Quienes dirigen una
    # célula sin figurar como integrantes de ella tampoco tienen célula como integrantes, así que
    # el ujier los ve (si no, nadie registraría su asistencia).
    assert [p["nombre"] for p in hoja["personas"]] == [
        "Daniel Jóvenes",
        "Eva Visitante",
        "Mario Libre",
        "Pedro Otro Líder",
        "Sofía Dirigente",
    ]


def test_el_ujier_de_otra_iglesia_ve_la_suya(mundo):
    por_id = hojas(pedir(mundo, "ujier_b"))
    assert [p["nombre"] for p in por_id[f"sin_celula:{mundo.iglesias['b']}"]["personas"]] == [
        "Carla Externa"
    ]


@pytest.mark.parametrize(
    "clave", ["presbitero", "pastor_a", "tesorero_a", "lider_red_a", "lider_sin_ficha"]
)
def test_los_demas_cargos_no_tienen_hojas(mundo, clave):
    assert pedir(mundo, clave).json() == []


# ---- El líder marca quién asistió ----


def test_el_lider_marca_quien_asistio_y_el_resto_queda_ausente(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    r = guardar(mundo, "lider_a", hoja, mundo.ids("jose"))
    assert r.status_code == 200, r.text
    assert r.json()["guardada"] is True
    assert marcados(r.json()) == ["José Pérez"]
    with mundo.fabrica() as sesion:
        por_miembro = {a.miembro_id: a for a in sesion.scalars(select(Asistencia))}
        assert por_miembro[mundo.miembros["jose"]].presente is True
        assert por_miembro[mundo.miembros["ana"]].presente is False
        assert por_miembro[mundo.miembros["jose"]].registrado_por == mundo.cuentas["lider_a"]
    assert marcados(hojas(pedir(mundo, "lider_a"))[hoja]) == ["José Pérez"]


def test_una_lista_con_nadie_marcado_tambien_queda_guardada(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    assert guardar(mundo, "lider_a", hoja, []).status_code == 200
    leida = hojas(pedir(mundo, "lider_a"))[hoja]
    assert leida["guardada"] is True
    assert marcados(leida) == []


def test_corregir_una_lista_no_duplica_las_marcas(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    guardar(mundo, "lider_a", hoja, mundo.ids("jose"))
    r = guardar(mundo, "lider_a", hoja, mundo.ids("ana", "jose"))
    assert marcados(r.json()) == ["Ana López", "José Pérez"]
    r = guardar(mundo, "lider_a", hoja, mundo.ids("ana"))
    assert marcados(r.json()) == ["Ana López"]
    assert filas(mundo) == 2  # una sola fila por persona, fecha y culto


def test_marcar_dos_veces_a_la_misma_persona_en_la_misma_peticion_cuenta_una_vez(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    r = guardar(mundo, "lider_a", hoja, [mundo.miembros["jose"]] * 3)
    assert r.status_code == 200
    assert filas(mundo) == 2


def test_cada_fecha_y_cada_culto_tienen_su_propia_lista(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    guardar(mundo, "lider_a", hoja, mundo.ids("jose"), fecha=HOY, servicio="culto_domingo")
    guardar(mundo, "lider_a", hoja, mundo.ids("ana"), fecha=HOY, servicio="culto_entre_semana")
    guardar(mundo, "lider_a", hoja, mundo.ids("jose", "ana"), fecha=AYER, servicio="culto_domingo")
    assert filas(mundo) == 6
    assert marcados(hojas(pedir(mundo, "lider_a", HOY, "culto_domingo"))[hoja]) == ["José Pérez"]
    assert marcados(hojas(pedir(mundo, "lider_a", HOY, "culto_entre_semana"))[hoja]) == [
        "Ana López"
    ]
    assert marcados(hojas(pedir(mundo, "lider_a", AYER, "culto_domingo"))[hoja]) == [
        "Ana López",
        "José Pérez",
    ]
    # Otra célula del mismo líder no se ve afectada.
    este = f"celula:{mundo.grupos['este']}"
    assert hojas(pedir(mundo, "lider_a", HOY, "culto_domingo"))[este]["guardada"] is False


# ---- El ujier marca quién faltó ----


def test_el_ujier_marca_quien_falto_y_el_resto_queda_presente(mundo):
    hoja = f"sin_celula:{mundo.iglesias['a']}"
    r = guardar(mundo, "ujier_a", hoja, mundo.ids("eva"))
    assert r.status_code == 200, r.text
    assert marcados(r.json()) == ["Eva Visitante"]
    with mundo.fabrica() as sesion:
        por_miembro = {a.miembro_id: a for a in sesion.scalars(select(Asistencia))}
        assert por_miembro[mundo.miembros["eva"]].presente is False
        assert por_miembro[mundo.miembros["mario"]].presente is True
    assert marcados(hojas(pedir(mundo, "ujier_a"))[hoja]) == ["Eva Visitante"]


# ---- Quién no puede marcar a quién ----


def test_el_lider_no_marca_a_quien_no_es_de_su_celula(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    for ajeno in ("tomas", "mario", "carla", "rut"):
        r = guardar(mundo, "lider_a", hoja, mundo.ids("jose", ajeno))
        assert r.status_code == 422, ajeno
    assert filas(mundo) == 0


def test_el_lider_no_usa_la_hoja_de_otro_lider(mundo):
    r = guardar(mundo, "lider_a", f"celula:{mundo.grupos['oeste']}", mundo.ids("tomas"))
    assert r.status_code == 403
    assert filas(mundo) == 0


def test_el_ujier_solo_marca_a_miembros_sin_celula_de_su_iglesia(mundo):
    hoja = f"sin_celula:{mundo.iglesias['a']}"
    for ajeno in ("jose", "luis", "carla"):  # con célula, inactivo y de otra iglesia
        r = guardar(mundo, "ujier_a", hoja, mundo.ids("eva", ajeno))
        assert r.status_code == 422, ajeno
    assert filas(mundo) == 0


def test_el_ujier_no_usa_la_hoja_de_otra_iglesia(mundo):
    r = guardar(mundo, "ujier_b", f"sin_celula:{mundo.iglesias['a']}", mundo.ids("eva"))
    assert r.status_code == 403
    assert filas(mundo) == 0


@pytest.mark.parametrize(
    "clave", ["presbitero", "pastor_a", "tesorero_a", "lider_red_a", "lider_sin_ficha"]
)
def test_los_demas_cargos_no_guardan_asistencia(mundo, clave):
    hoja = f"celula:{mundo.grupos['norte']}"
    assert guardar(mundo, clave, hoja, mundo.ids("jose")).status_code == 403
    assert filas(mundo) == 0


def test_quien_ya_no_dirige_la_celula_pierde_la_hoja(mundo):
    with mundo.fabrica() as sesion:
        sesion.get(Grupo, mundo.grupos["norte"]).lider_miembro_id = mundo.miembros["jose"]
        sesion.commit()
    hoja = f"celula:{mundo.grupos['norte']}"
    assert guardar(mundo, "lider_a", hoja, mundo.ids("jose")).status_code == 403


def test_una_celula_inactiva_ya_no_tiene_hoja(mundo):
    with mundo.fabrica() as sesion:
        sesion.get(Grupo, mundo.grupos["este"]).activo = False
        sesion.commit()
    assert list(hojas(pedir(mundo, "lider_a"))) == [f"celula:{mundo.grupos['norte']}"]


# ---- Validaciones ----


@pytest.mark.parametrize("servicio", TIPOS_SERVICIO_ASISTENCIA)
def test_acepta_todos_los_cultos_de_la_lista(mundo, servicio):
    hoja = f"celula:{mundo.grupos['norte']}"
    assert guardar(mundo, "lider_a", hoja, mundo.ids("jose"), servicio=servicio).status_code == 200
    assert pedir(mundo, "lider_a", servicio=servicio).status_code == 200


def test_rechaza_cultos_y_fechas_no_validos(mundo):
    hoja = f"celula:{mundo.grupos['norte']}"
    manana = HOY + timedelta(days=2)
    assert guardar(mundo, "lider_a", hoja, [], servicio="funeral").status_code == 422
    assert guardar(mundo, "lider_a", hoja, [], fecha=manana).status_code == 422
    assert pedir(mundo, "lider_a", servicio="funeral").status_code == 422
    assert pedir(mundo, "lider_a", fecha=manana).status_code == 422
    assert (
        mundo.cliente.get(
            "/asistencia?fecha=ayer&servicio=culto_domingo", headers=mundo.cab("lider_a")
        ).status_code
        == 422
    )
    assert filas(mundo) == 0


def test_no_se_aceptan_campos_desconocidos_y_el_error_no_repite_lo_enviado(mundo):
    cuerpo = {
        "fecha": str(HOY),
        "servicio": "culto_domingo",
        "hoja": f"celula:{mundo.grupos['norte']}",
        "marcados": [],
        "comentario": "texto-privado",
    }
    r = mundo.cliente.put("/asistencia", json=cuerpo, headers=mundo.cab("lider_a"))
    assert r.status_code == 422
    assert "texto-privado" not in r.text
