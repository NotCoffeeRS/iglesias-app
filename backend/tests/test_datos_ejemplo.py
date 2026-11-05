"""Pruebas del script de datos de ejemplo (Issue #5).

Lo que se comprueba:
  - Que cargue lo prometido: 4 iglesias, 5 sedes (la 3ra con Madero y Kanasín), 6 cuentas con
    su cargo, la cuenta del líder ligada a su ficha de miembro, miembros, grupos, ingresos y gastos.
  - Que sea REPETIBLE: correrlo dos veces no duplica nada ni cambia contraseñas ya guardadas.
  - Que NO invente lo que aún no tenemos: sin horarios, redes sociales ni fotos.
  - Que las contraseñas salgan solo de variables de entorno (nunca del código) y que no
    se impriman; que falle con un mensaje claro si falta una o es muy corta.
  - Que solo corra contra una base local y que exija --confirmar.

Igual que test_modelos.py, estas pruebas necesitan PostgreSQL de verdad y trabajan en bases
temporales que se crean y se borran solas: no tocan tus datos. Las contraseñas de las pruebas se
inventan al azar en cada corrida; no hay ninguna escrita en este archivo.
"""

import re
import secrets
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from alembic import command
from app.modelos import (
    Gasto,
    Grupo,
    GrupoMiembro,
    Horario,
    Iglesia,
    Ingreso,
    Miembro,
    RedSocial,
    Sede,
    Usuario,
)
from app.modelos.utilidades import obtener_url_base_datos
from app.seguridad.contrasenas import verificar_contrasena
from scripts import cargar_datos_ejemplo as script
from scripts.cargar_datos_ejemplo import (
    GASTOS,
    IGLESIA_DEMO,
    INGRESOS,
    VARIABLES_CLAVE,
    ErrorDatosEjemplo,
    cargar_datos,
    leer_claves,
    main,
    validar_base_local,
)

# Rutas de backend/alembic.ini y del script (este archivo está en backend/tests/).
RUTA_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
RUTA_SCRIPT = Path(script.__file__)

CARGOS_ESPERADOS = {"presbitero", "pastor", "apoyo_pastor", "tesorero", "lider_celula", "ujier"}

MENSAJE_SIN_POSTGRES = (
    "No hay una base PostgreSQL configurada para las pruebas. Define DATABASE_URL en el "
    "entorno o en backend/.env, por ejemplo: "
    "postgresql+psycopg://postgres:TU_CONTRASENA@localhost:5432/postgres ."
)
MENSAJE_SIN_CONEXION = (
    "No se pudo crear la base temporal de pruebas en PostgreSQL. Revisa que el servicio "
    "esté corriendo, que la contraseña de DATABASE_URL sea la correcta y que ese usuario "
    "pueda crear bases de datos (CREATEDB)."
)


# ---------------------------------------------------------------------------
# Ayudas y fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def url_servidor() -> URL:
    """URL del servidor PostgreSQL; si no hay una, la prueba falla con un mensaje claro."""
    texto = obtener_url_base_datos()
    if not texto or not texto.startswith("postgresql"):
        pytest.fail(MENSAJE_SIN_POSTGRES, pytrace=False)
    return make_url(texto)


@contextmanager
def _base_temporal(url_servidor: URL, migrar: bool = True) -> Iterator[URL]:
    """Crea una base vacía con nombre único (migrada si se pide) y la borra al terminar."""
    nombre = f"iglesias_prueba_{uuid.uuid4().hex[:12]}"
    # AUTOCOMMIT: CREATE/DROP DATABASE no pueden ir dentro de una transacción.
    motor_admin = create_engine(url_servidor, isolation_level="AUTOCOMMIT")
    try:
        fallo = False
        try:
            with motor_admin.connect() as conexion:
                conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
        except DBAPIError:
            fallo = True
        if fallo:
            # Se avisa fuera del except para no mostrar el error original (datos de conexión).
            pytest.fail(MENSAJE_SIN_CONEXION, pytrace=False)
        try:
            url = url_servidor.set(database=nombre)
            if migrar:
                config = Config(str(RUTA_ALEMBIC_INI))
                config.attributes["url"] = url
                command.upgrade(config, "head")
            yield url
        finally:
            with motor_admin.connect() as conexion:
                conexion.execute(text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)'))
    finally:
        motor_admin.dispose()


@pytest.fixture(scope="module")
def claves() -> dict[str, str]:
    """Contraseñas inventadas al azar para esta corrida: {cargo: contraseña}."""
    return {cargo: secrets.token_urlsafe(18) for cargo in VARIABLES_CLAVE}


@pytest.fixture(scope="module")
def base_cargada(url_servidor: URL, claves: dict[str, str]) -> Iterator[dict]:
    """Una base temporal migrada con los datos de ejemplo ya cargados una vez."""
    with _base_temporal(url_servidor) as url:
        motor = create_engine(url)
        with Session(motor) as sesion, sesion.begin():
            resumen = cargar_datos(sesion, claves)
        yield {"motor": motor, "resumen": resumen}
        motor.dispose()


@pytest.fixture
def sesion(base_cargada: dict) -> Iterator[Session]:
    """Sesión de lectura; todo lo que haga se deshace al terminar (no deja rastro)."""
    conexion = base_cargada["motor"].connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion)
    try:
        yield sesion
    finally:
        sesion.close()
        if transaccion.is_active:
            transaccion.rollback()
        conexion.close()


@pytest.fixture(scope="module")
def base_vacia(url_servidor: URL) -> Iterator[URL]:
    """Una base temporal migrada y SIN datos, para pruebas que no deben cargar nada."""
    with _base_temporal(url_servidor) as url:
        yield url


@pytest.fixture
def entorno(monkeypatch: pytest.MonkeyPatch, claves: dict[str, str]) -> None:
    """Define en el entorno las 6 variables de contraseña, como lo haría Jessica en su terminal."""
    for cargo, variable in VARIABLES_CLAVE.items():
        monkeypatch.setenv(variable, claves[cargo])


def _apuntar_a(monkeypatch: pytest.MonkeyPatch, url: URL) -> None:
    """Hace que el script use esta base (DATABASE_URL) sin tocar ningún archivo."""
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))


def _contar(sesion: Session, modelo: type) -> int:
    """Cuántas filas tiene la tabla del modelo."""
    return sesion.scalar(select(func.count()).select_from(modelo))


def _cuenta(sesion: Session, cargo: str) -> Usuario:
    """La cuenta de ejemplo de ese cargo."""
    return sesion.scalars(select(Usuario).where(Usuario.cargo == cargo)).one()


# ---------------------------------------------------------------------------
# Qué se carga
# ---------------------------------------------------------------------------


def test_cuatro_iglesias_con_su_pastor(sesion: Session) -> None:
    """Las 4 iglesias del Presbiterio, con el pastor (dato público)."""
    pastores = {i.nombre: i.pastor for i in sesion.scalars(select(Iglesia))}
    assert pastores == {
        "3ra IAFCJ de Mérida": "Jorge Lozano",
        "4ta IAFCJ de Mérida": "Isaac Euan",
        "6ta IAFCJ de Mérida": "Manuel Ortega",
        "IAFCJ de Huhí": "Jeremías Camaal",
    }


def test_cinco_sedes_y_la_3ra_tiene_madero_y_kanasin(sesion: Session) -> None:
    """Son 5 sedes en total; solo la 3ra de Mérida tiene dos (Madero y Kanasín)."""
    assert _contar(sesion, Sede) == 5
    sedes_3ra = sesion.scalars(
        select(Sede.nombre).join(Iglesia).where(Iglesia.nombre == IGLESIA_DEMO)
    ).all()
    assert sorted(sedes_3ra) == ["Kanasín", "Madero"]
    # Las otras tres iglesias tienen una sola sede cada una.
    cuentas = sesion.execute(
        select(Iglesia.nombre, func.count(Sede.id)).join(Sede).group_by(Iglesia.nombre)
    ).all()
    assert {nombre: total for nombre, total in cuentas if nombre != IGLESIA_DEMO} == {
        "4ta IAFCJ de Mérida": 1,
        "6ta IAFCJ de Mérida": 1,
        "IAFCJ de Huhí": 1,
    }


def test_no_se_inventan_direcciones_horarios_redes_ni_fotos(sesion: Session) -> None:
    """Lo que aún no tenemos queda como "Por confirmar" o vacío; nada inventado."""
    assert set(sesion.scalars(select(Sede.direccion))) == {"Por confirmar"}
    assert set(sesion.scalars(select(Sede.enlace_maps))) == {None}
    assert _contar(sesion, Horario) == 0
    assert _contar(sesion, RedSocial) == 0
    assert set(sesion.scalars(select(Iglesia.foto_url))) == {None}
    assert set(sesion.scalars(select(Iglesia.telefono_pastor))) == {None}
    assert set(sesion.scalars(select(Iglesia.telefono_iglesia))) == {None}


def test_seis_cuentas_una_por_cargo(sesion: Session) -> None:
    """Hay exactamente 6 cuentas y cada cargo aparece una vez."""
    cargos = sesion.scalars(select(Usuario.cargo)).all()
    assert sorted(cargos) == sorted(CARGOS_ESPERADOS)
    assert all(sesion.scalars(select(Usuario.activo)))


def test_las_cuentas_pertenecen_a_la_iglesia_correcta(sesion: Session) -> None:
    """El presbítero no tiene iglesia; las otras 5 cuentas son de la 3ra de Mérida."""
    demo = sesion.scalars(select(Iglesia).where(Iglesia.nombre == IGLESIA_DEMO)).one()
    assert _cuenta(sesion, "presbitero").iglesia_id is None
    for cargo in CARGOS_ESPERADOS - {"presbitero"}:
        assert _cuenta(sesion, cargo).iglesia_id == demo.id


def test_la_cuenta_del_lider_esta_ligada_a_su_ficha_de_miembro(sesion: Session) -> None:
    """Decisión D21: el líder de célula tiene miembro_id y esa ficha dirige la célula."""
    lider = _cuenta(sesion, "lider_celula")
    assert lider.miembro_id is not None
    celula = sesion.scalars(select(Grupo).where(Grupo.tipo == "celula")).one()
    assert celula.lider_miembro_id == lider.miembro_id
    ficha = sesion.get(Miembro, lider.miembro_id)
    assert ficha.iglesia_id == lider.iglesia_id
    # Las demás cuentas no se ligan a ninguna ficha.
    otras = sesion.scalars(select(Usuario).where(Usuario.cargo != "lider_celula")).all()
    assert all(cuenta.miembro_id is None for cuenta in otras)


def test_miembros_y_grupos(sesion: Session) -> None:
    """Hay miembros con distintos estados y los 6 grupos de la 3ra de Mérida."""
    assert _contar(sesion, Miembro) == 22
    estados = set(sesion.scalars(select(Miembro.estado)))
    assert {"activo", "visitante", "inactivo", "en_proceso_ganar"} <= estados
    tipos = sorted(sesion.scalars(select(Grupo.tipo)))
    assert tipos == ["area", "celula", "ministerio", "red", "red", "red"]


def test_hay_miembros_sin_celula_para_la_pantalla_del_ujier(sesion: Session) -> None:
    """El ujier marca a quienes no tienen célula: debe haber varios miembros activos así."""
    en_celula = select(GrupoMiembro.miembro_id).where(GrupoMiembro.tipo_grupo == "celula")
    sin_celula = sesion.scalars(
        select(Miembro).where(Miembro.estado == "activo", Miembro.id.not_in(en_celula))
    ).all()
    assert len(sin_celula) >= 3


def test_ingresos_y_gastos_ficticios_en_las_4_iglesias(sesion: Session) -> None:
    """Todo el dinero es positivo, hay en las 4 iglesias y lo registra la cuenta esperada."""
    assert _contar(sesion, Ingreso) == len(INGRESOS)
    assert _contar(sesion, Gasto) == len(GASTOS)
    assert all(monto > Decimal("0") for monto in sesion.scalars(select(Ingreso.monto)))
    assert all(monto > Decimal("0") for monto in sesion.scalars(select(Gasto.monto)))

    iglesias = {i.nombre: i.id for i in sesion.scalars(select(Iglesia))}
    tesorero, presbitero = _cuenta(sesion, "tesorero"), _cuenta(sesion, "presbitero")
    for modelo in (Ingreso, Gasto):
        for nombre, iglesia_id in iglesias.items():
            quienes = set(
                sesion.scalars(select(modelo.registrado_por).where(modelo.iglesia_id == iglesia_id))
            )
            # La 3ra la registra el tesorero; las otras, la cuenta del presbítero.
            esperado = tesorero.id if nombre == IGLESIA_DEMO else presbitero.id
            assert quienes == {esperado}, f"{modelo.__name__} de {nombre}"


def test_un_gasto_viene_anulado_con_motivo_y_ningun_ingreso(sesion: Session) -> None:
    """Un gasto de ejemplo ya está anulado (con motivo y quién); nada se borra."""
    anulados = sesion.scalars(select(Gasto).where(Gasto.anulado_en.is_not(None))).all()
    assert len(anulados) == 1
    assert anulados[0].anulado_motivo
    assert anulados[0].anulado_por == _cuenta(sesion, "tesorero").id
    ingresos_anulados = sesion.scalar(
        select(func.count()).select_from(Ingreso).where(Ingreso.anulado_en.is_not(None))
    )
    assert ingresos_anulados == 0


def test_cada_ingreso_y_gasto_lleva_su_etiqueta_unica(sesion: Session) -> None:
    """La etiqueta [ejemplo-...] es lo que permite reconocerlos al repetir el script."""
    descripciones = sesion.scalars(select(Ingreso.descripcion)).all()
    notas = sesion.scalars(select(Gasto.nota)).all()
    etiquetas = [
        re.match(r"\[ejemplo-(?:ING|GAS)-\d+\]", t).group(0) for t in descripciones + notas
    ]
    assert len(etiquetas) == len(set(etiquetas))


# ---------------------------------------------------------------------------
# Repetible (no duplica)
# ---------------------------------------------------------------------------


def test_correrlo_dos_veces_no_duplica_nada(sesion: Session, base_cargada: dict) -> None:
    """Una segunda corrida no crea ninguna fila y las tablas quedan con los mismos totales."""
    modelos = (Iglesia, Sede, Miembro, Usuario, Grupo, GrupoMiembro, Ingreso, Gasto)
    antes = {modelo.__name__: _contar(sesion, modelo) for modelo in modelos}
    # La primera corrida (en la fixture) sí creó cosas en todas las tablas.
    assert all(cuenta["creados"] > 0 for cuenta in base_cargada["resumen"].values())

    claves_nuevas = {cargo: secrets.token_urlsafe(18) for cargo in VARIABLES_CLAVE}
    resumen = cargar_datos(sesion, claves_nuevas)
    assert all(cuenta["creados"] == 0 for cuenta in resumen.values()), dict(resumen)
    despues = {modelo.__name__: _contar(sesion, modelo) for modelo in modelos}
    assert antes == despues


# ---------------------------------------------------------------------------
# Contraseñas
# ---------------------------------------------------------------------------


def test_las_contrasenas_guardadas_son_hashes_de_las_variables_de_entorno(
    sesion: Session, claves: dict[str, str]
) -> None:
    """Cada cuenta guarda un hash Argon2id que verifica con SU contraseña, nunca el texto."""
    for cargo, clave in claves.items():
        cuenta = _cuenta(sesion, cargo)
        assert cuenta.contrasena_hash.startswith("$argon2")
        assert clave not in cuenta.contrasena_hash
        assert verificar_contrasena(clave, cuenta.contrasena_hash)
        # Y no verifica con la de otro cargo: cada cuenta tiene la suya.
        otra = claves["ujier" if cargo != "ujier" else "pastor"]
        assert not verificar_contrasena(otra, cuenta.contrasena_hash)


def test_una_cuenta_existente_conserva_su_contrasena(
    sesion: Session, claves: dict[str, str]
) -> None:
    """Si la cuenta ya existe, correr el script con otras contraseñas no se las cambia."""
    nueva = {cargo: secrets.token_urlsafe(18) for cargo in VARIABLES_CLAVE}
    cargar_datos(sesion, nueva)
    cuenta = _cuenta(sesion, "tesorero")
    assert verificar_contrasena(claves["tesorero"], cuenta.contrasena_hash)
    assert not verificar_contrasena(nueva["tesorero"], cuenta.contrasena_hash)


def test_el_codigo_no_tiene_contrasenas_escritas() -> None:
    """El script no asigna ninguna contraseña literal y menciona las 6 variables de entorno."""
    codigo = RUTA_SCRIPT.read_text(encoding="utf-8")
    # Busca cosas como  clave = "algo"  o  contrasena_x = 'algo'.
    asignaciones = re.findall(r"""(?i)(?:clave|contrasena|password)\w*\s*=\s*["']""", codigo)
    assert asignaciones == []
    for variable in VARIABLES_CLAVE.values():
        assert variable in codigo


def test_falta_una_variable_da_un_mensaje_claro() -> None:
    """Sin variables, el error nombra TODAS las que faltan (solo sus nombres)."""
    with pytest.raises(ErrorDatosEjemplo) as error:
        leer_claves({})
    for variable in VARIABLES_CLAVE.values():
        assert variable in str(error.value)


def test_falta_solo_una_variable_y_solo_esa_se_nombra() -> None:
    """Si falta una, el mensaje nombra esa y no las demás; una vacía cuenta como faltante."""
    entorno = {variable: "x" * 20 for variable in VARIABLES_CLAVE.values()}
    entorno["EJEMPLO_CLAVE_UJIER"] = ""
    with pytest.raises(ErrorDatosEjemplo) as error:
        leer_claves(entorno)
    assert "EJEMPLO_CLAVE_UJIER" in str(error.value)
    assert "EJEMPLO_CLAVE_PASTOR" not in str(error.value)


def test_una_contrasena_corta_se_rechaza_sin_mostrar_su_valor() -> None:
    """Menos de 12 caracteres: se rechaza y el mensaje no repite el valor."""
    entorno = {variable: "x" * 20 for variable in VARIABLES_CLAVE.values()}
    entorno["EJEMPLO_CLAVE_APOYO"] = "Zq7corta"
    with pytest.raises(ErrorDatosEjemplo) as error:
        leer_claves(entorno)
    assert "EJEMPLO_CLAVE_APOYO" in str(error.value)
    assert "Zq7" not in str(error.value)


def test_con_las_6_variables_correctas_devuelve_una_clave_por_cargo(
    claves: dict[str, str],
) -> None:
    """Con todo bien, `leer_claves` devuelve {cargo: contraseña} sin cambiarlas."""
    entorno = {VARIABLES_CLAVE[cargo]: clave for cargo, clave in claves.items()}
    assert leer_claves(entorno) == claves


# ---------------------------------------------------------------------------
# Seguridad de la base destino
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("host", [None, "localhost", "127.0.0.1", "::1"])
def test_bases_locales_se_aceptan(host: str | None) -> None:
    """Una base en esta misma computadora pasa la validación."""
    validar_base_local(URL.create("postgresql+psycopg", host=host, database="x"))


@pytest.mark.parametrize(
    "url",
    [
        URL.create("postgresql+psycopg", host="servidor.ejemplo.invalid", database="x"),
        URL.create("postgresql+psycopg", host="10.0.0.5", database="x"),
        # Un host escondido en el parámetro ?host= también cuenta.
        URL.create(
            "postgresql+psycopg", host="localhost", database="x", query={"host": "otro.invalid"}
        ),
    ],
)
def test_bases_remotas_se_rechazan(url: URL) -> None:
    """Cualquier base que no sea local detiene el script."""
    with pytest.raises(ErrorDatosEjemplo, match="no es local"):
        validar_base_local(url)


# ---------------------------------------------------------------------------
# El programa completo (main)
# ---------------------------------------------------------------------------


def _texto_de_salida(capsys: pytest.CaptureFixture[str]) -> str:
    """Todo lo que el script imprimió (pantalla normal y de errores)."""
    salida = capsys.readouterr()
    return salida.out + salida.err


def test_sin_confirmar_no_se_toca_la_base(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entorno: None,
    base_vacia: URL,
) -> None:
    """Sin --confirmar solo muestra el nombre de la base y se detiene."""
    _apuntar_a(monkeypatch, base_vacia)
    assert main([]) == 1
    texto = _texto_de_salida(capsys)
    assert base_vacia.database in texto
    assert "--confirmar" in texto
    motor = create_engine(base_vacia)
    with Session(motor) as sesion:
        assert _contar(sesion, Iglesia) == 0
        assert _contar(sesion, Usuario) == 0
    motor.dispose()


def test_falta_una_variable_y_main_no_toca_la_base(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entorno: None,
    base_vacia: URL,
) -> None:
    """Con --confirmar pero sin una contraseña, se detiene con un mensaje claro y no carga nada."""
    _apuntar_a(monkeypatch, base_vacia)
    monkeypatch.delenv("EJEMPLO_CLAVE_TESORERO")
    assert main(["--confirmar"]) == 1
    texto = _texto_de_salida(capsys)
    assert "EJEMPLO_CLAVE_TESORERO" in texto
    motor = create_engine(base_vacia)
    with Session(motor) as sesion:
        assert _contar(sesion, Iglesia) == 0
    motor.dispose()


def test_main_rechaza_una_base_que_no_es_local(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], entorno: None
) -> None:
    """Una DATABASE_URL remota detiene el script y no se imprime ni el servidor ni la contraseña."""
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://alguien:secreta-9x@servidor.ejemplo.invalid:5432/otra"
    )
    assert main(["--confirmar"]) == 1
    texto = _texto_de_salida(capsys)
    assert "no es local" in texto
    assert "servidor.ejemplo.invalid" not in texto
    assert "secreta-9x" not in texto


def test_main_avisa_si_faltan_las_migraciones(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entorno: None,
    url_servidor: URL,
) -> None:
    """En una base sin tablas no hace nada y explica que primero hay que migrar."""
    with _base_temporal(url_servidor, migrar=False) as url:
        _apuntar_a(monkeypatch, url)
        assert main(["--confirmar"]) == 1
        assert "migraciones" in _texto_de_salida(capsys)


def test_main_carga_y_repite_sin_imprimir_contrasenas(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entorno: None,
    claves: dict[str, str],
    url_servidor: URL,
) -> None:
    """Con --confirmar carga todo; al repetirlo no crea nada; nunca imprime secretos."""
    with _base_temporal(url_servidor) as url:
        _apuntar_a(monkeypatch, url)
        assert main(["--confirmar"]) == 0
        primera = _texto_de_salida(capsys)
        assert main(["--confirmar"]) == 0
        segunda = _texto_de_salida(capsys)

        assert "usuarios: 6 creadas, 0 ya existían" in primera
        assert "usuarios: 0 creadas, 6 ya existían" in segunda
        assert "ingresos: 0 creadas" in segunda

        # Ni las contraseñas, ni la URL de conexión (ni la contraseña del servidor) aparecen.
        for texto in (primera, segunda):
            assert url.database in texto
            assert "postgresql" not in texto
            for clave in claves.values():
                assert clave not in texto
            if url.password:
                assert url.password not in texto
