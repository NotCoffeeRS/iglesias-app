"""Carga datos de ejemplo para la demo (Issue #5, tarea T-06).

Qué carga (todo inventado, salvo los datos públicos de las iglesias):
  - Las 4 iglesias del Presbiterio con sus 5 sedes (la 3ra de Mérida tiene Madero y Kanasín).
  - Miembros ficticios, grupos (célula, redes, ministerio y área) y quién está en cada uno.
  - 6 cuentas de ejemplo, una por cargo: presbítero, pastor, apoyo del pastor, tesorero,
    líder de célula y ujier.
  - Ingresos y gastos ficticios de octubre y noviembre de 2026.

Qué NO carga (todavía no tenemos esos datos y no se inventan): direcciones reales, enlaces
de Google Maps, horarios, redes sociales, fotos ni teléfonos de las iglesias. La dirección
de cada sede queda como "Por confirmar".

Es REPETIBLE: antes de insertar cada fila busca si ya existe y, si existe, la deja igual.
Nunca borra ni modifica nada, así que se puede correr dos veces sin duplicar.

CONTRASEÑAS: no están en el código ni en ningún archivo. Se leen de estas 6 variables de
entorno, que se definen en la terminal antes de correr el script (una por cuenta):

    EJEMPLO_CLAVE_PRESBITERO   EJEMPLO_CLAVE_PASTOR    EJEMPLO_CLAVE_APOYO
    EJEMPLO_CLAVE_TESORERO     EJEMPLO_CLAVE_LIDER_CELULA    EJEMPLO_CLAVE_UJIER

Cada una debe tener al menos 12 caracteres. El script solo guarda el hash (Argon2id) y nunca
imprime las contraseñas. Si una cuenta ya existe, NO se le cambia la contraseña.

SEGURIDAD: solo corre contra un PostgreSQL de esta misma computadora (localhost) y exige
la bandera --confirmar. Muestra el NOMBRE de la base destino, nunca la URL de conexión.
Tampoco aplica migraciones: la base debe estar ya en la versión más reciente.

Uso (desde la carpeta backend, con DATABASE_URL en el entorno o en backend/.env):

    python -m scripts.cargar_datos_ejemplo              (solo muestra el destino y se detiene)
    python -m scripts.cargar_datos_ejemplo --confirmar  (carga los datos)
"""

import argparse
import os
import sys
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from datetime import date

from sqlalchemy import func, inspect, select
from sqlalchemy.engine import URL, create_engine, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.modelos import Grupo, GrupoMiembro, Iglesia, Miembro, Sede, Usuario
from app.modelos.utilidades import obtener_url_base_datos
from app.seguridad.contrasenas import crear_hash

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Variable de entorno que trae la contraseña de cada cuenta de ejemplo, según su cargo.
VARIABLES_CLAVE = {
    "presbitero": "EJEMPLO_CLAVE_PRESBITERO",
    "pastor": "EJEMPLO_CLAVE_PASTOR",
    "apoyo_pastor": "EJEMPLO_CLAVE_APOYO",
    "tesorero": "EJEMPLO_CLAVE_TESORERO",
    "lider_celula": "EJEMPLO_CLAVE_LIDER_CELULA",
    "ujier": "EJEMPLO_CLAVE_UJIER",
}

# Una contraseña más corta que esto se rechaza antes de tocar la base.
LARGO_MINIMO_CLAVE = 12

# Nombres de equipo que cuentan como "esta misma computadora".
HOSTS_LOCALES = {"localhost", "127.0.0.1", "::1"}

# Texto que se guarda mientras no tengamos la dirección real de una sede (Issue #5).
POR_CONFIRMAR = "Por confirmar"

# Tablas que deben existir (las crea Alembic). Si falta alguna, el script no hace nada.
TABLAS_REQUERIDAS = {
    "iglesias",
    "sedes",
    "miembros",
    "usuarios",
    "grupos",
    "grupo_miembros",
    "ingresos",
    "gastos",
}

# Las 4 iglesias del Presbiterio. Nombre de la iglesia y pastor son datos públicos
# (AGENTS.md, regla 9); las sedes llevan dirección "Por confirmar".
# OJO: los nombres exactos de la 4ta, la 6ta y Huhí son una propuesta, pendiente de confirmar.
IGLESIAS = (
    {
        "nombre": "3ra IAFCJ de Mérida",
        "pastor": "Jorge Lozano",
        "sedes": ("Madero", "Kanasín"),
    },
    {"nombre": "4ta IAFCJ de Mérida", "pastor": "Isaac Euan", "sedes": ("Sede única",)},
    {"nombre": "6ta IAFCJ de Mérida", "pastor": "Manuel Ortega", "sedes": ("Sede única",)},
    {"nombre": "IAFCJ de Huhí", "pastor": "Jeremías Camaal", "sedes": ("Sede única",)},
)

# Nombre de la iglesia "principal" de la demo: ahí viven las 5 cuentas con iglesia.
IGLESIA_DEMO = "3ra IAFCJ de Mérida"

# Miembros ficticios. Cada uno: (nombre, estado, estado civil, nacimiento, bautizo, ingreso).
# Todo es inventado; los nombres son únicos dentro de cada iglesia (así se reconocen al repetir).
# Los teléfonos y correos se generan abajo con formatos que no existen (555-... y example.com).
MIEMBROS = {
    "3ra IAFCJ de Mérida": (
        (
            "Marta Elena Canul Pech",
            "activo",
            "casado",
            date(1984, 3, 12),
            date(2006, 5, 7),
            date(2005, 1, 9),
        ),
        (
            "Rosa Isela Chan May",
            "activo",
            "casado",
            date(1990, 7, 25),
            date(2010, 8, 15),
            date(2009, 2, 1),
        ),
        (
            "Carlos Alberto Dzul Uc",
            "activo",
            "casado",
            date(1979, 11, 2),
            date(2001, 4, 22),
            date(2000, 6, 4),
        ),
        (
            "Lucía Fernanda Poot Kú",
            "activo",
            "soltero",
            date(1998, 1, 30),
            date(2015, 9, 6),
            date(2014, 3, 2),
        ),
        (
            "Daniel Esteban Cime Tun",
            "activo",
            "soltero",
            date(2001, 6, 18),
            date(2018, 12, 2),
            date(2017, 5, 7),
        ),
        (
            "Sofía Guadalupe Euán Cauich",
            "activo",
            "soltero",
            date(2003, 9, 9),
            date(2019, 7, 14),
            date(2018, 8, 5),
        ),
        (
            "Miguel Ángel Balam Chi",
            "activo",
            "casado",
            date(1975, 4, 5),
            date(1999, 10, 3),
            date(1998, 2, 8),
        ),
        (
            "Elena Beatriz Cocom Ek",
            "activo",
            "viudo",
            date(1968, 12, 21),
            date(1995, 6, 11),
            date(1994, 1, 2),
        ),
        (
            "Josué Emanuel Pat Yam",
            "activo",
            "soltero",
            date(2000, 2, 14),
            date(2016, 11, 13),
            date(2015, 4, 19),
        ),
        (
            "Abigail Noemí Tzec Moo",
            "activo",
            "soltero",
            date(1999, 8, 3),
            date(2017, 3, 5),
            date(2016, 9, 4),
        ),
        ("Ricardo Iván Ay Sosa", "visitante", None, date(1992, 5, 27), None, None),
        (
            "Paola Andrea Kantún Ceh",
            "en_proceso_ganar",
            "union_libre",
            date(1995, 10, 8),
            None,
            date(2026, 8, 2),
        ),
        (
            "Hugo Armando Mex Dzib",
            "en_proceso_discipular",
            "casado",
            date(1987, 1, 16),
            None,
            date(2026, 3, 1),
        ),
        (
            "Teresa de Jesús Be Couoh",
            "inactivo",
            "divorciado",
            date(1971, 9, 29),
            date(2003, 7, 20),
            date(2002, 5, 5),
        ),
        (
            "Samuel David Chulim Pool",
            "en_proceso_consolidar",
            "casado",
            date(1983, 12, 4),
            None,
            date(2026, 5, 3),
        ),
    ),
    "4ta IAFCJ de Mérida": (
        (
            "Andrés Felipe Kauil Mis",
            "activo",
            "casado",
            date(1981, 6, 10),
            date(2004, 3, 14),
            date(2003, 8, 3),
        ),
        (
            "Karla Yamileth Tamay Ake",
            "activo",
            "soltero",
            date(1996, 4, 23),
            date(2014, 10, 5),
            date(2013, 2, 3),
        ),
        ("Pedro Antonio Xool Pech", "visitante", None, date(1989, 8, 19), None, None),
    ),
    "6ta IAFCJ de Mérida": (
        (
            "Verónica Alejandra Ucán Dzul",
            "activo",
            "casado",
            date(1986, 2, 8),
            date(2008, 6, 1),
            date(2007, 4, 1),
        ),
        (
            "Fernando Ismael Cab Canché",
            "en_proceso_ganar",
            "soltero",
            date(1997, 11, 11),
            None,
            date(2026, 9, 6),
        ),
    ),
    "IAFCJ de Huhí": (
        (
            "Rubí Esmeralda Mukul Pat",
            "activo",
            "soltero",
            date(1994, 3, 3),
            date(2012, 5, 20),
            date(2011, 1, 16),
        ),
        (
            "Gael Eduardo Sulub May",
            "activo",
            "casado",
            date(1980, 7, 7),
            date(2002, 9, 8),
            date(2001, 3, 4),
        ),
    ),
}

# Correos de ejemplo solo para algunos miembros (example.com es un dominio reservado).
CORREOS = {
    "Marta Elena Canul Pech": "marta.canul@example.com",
    "Carlos Alberto Dzul Uc": "carlos.dzul@example.com",
}

# Las 6 cuentas de ejemplo: (cargo, nombre de usuario, nombre completo, ¿pertenece a una iglesia?).
# El presbítero es el único cargo que puede no tener iglesia. Los nombres no son de personas
# reales. La del líder de célula usa el nombre de su ficha de miembro (ver CUENTA_LIGADA).
CUENTAS = (
    ("presbitero", "presbitero.ejemplo", "Presbítero de ejemplo", False),
    ("pastor", "pastor.ejemplo", "Pastor de ejemplo", True),
    ("apoyo_pastor", "apoyo.ejemplo", "Apoyo del pastor de ejemplo", True),
    ("tesorero", "tesorero.ejemplo", "Tesorero de ejemplo", True),
    ("lider_celula", "lider.celula.ejemplo", "Marta Elena Canul Pech", True),
    ("ujier", "ujier.ejemplo", "Ujier de ejemplo", True),
)

# Decisión D21: el "área" de un usuario sale de los grupos que dirige su ficha de miembro.
# Por eso la cuenta del líder de célula se liga (miembro_id) a la ficha de este miembro.
CUENTA_LIGADA = {"lider_celula": "Marta Elena Canul Pech"}

# Grupos de la iglesia de la demo: (tipo, nombre, líder, asistente). El líder es siempre
# un miembro (no un usuario) y no puede ser la misma persona que el asistente.
GRUPOS = (
    ("celula", "Célula Betania", "Marta Elena Canul Pech", "Rosa Isela Chan May"),
    ("red", "Red de Damas", "Elena Beatriz Cocom Ek", "Sofía Guadalupe Euán Cauich"),
    ("red", "Red de Varones", "Miguel Ángel Balam Chi", "Daniel Esteban Cime Tun"),
    ("red", "Red de Jóvenes", "Josué Emanuel Pat Yam", "Abigail Noemí Tzec Moo"),
    ("ministerio", "Ministerio de Alabanza", "Abigail Noemí Tzec Moo", "Josué Emanuel Pat Yam"),
    ("area", "Tiendita", "Samuel David Chulim Pool", None),
)

# Quién está en cada grupo (además de su líder y asistente, que se agregan solos).
# Un miembro solo puede estar en UNA célula; los demás miembros quedan "sin célula" y son
# los que ve el ujier. En la célula también entra su líder, para que no salga en esa lista.
INTEGRANTES = {
    "Célula Betania": (
        "Carlos Alberto Dzul Uc",
        "Lucía Fernanda Poot Kú",
        "Daniel Esteban Cime Tun",
        "Sofía Guadalupe Euán Cauich",
    ),
    "Ministerio de Alabanza": ("Sofía Guadalupe Euán Cauich",),
}


class ErrorDatosEjemplo(Exception):
    """Un problema que se explica al usuario en español (sin trazas ni datos sensibles)."""


# ---------------------------------------------------------------------------
# Seguridad: contraseñas y base de datos destino
# ---------------------------------------------------------------------------


def leer_claves(entorno: Mapping[str, str]) -> dict[str, str]:
    """Lee las 6 contraseñas del entorno y devuelve {cargo: contraseña}.

    Si falta alguna o es muy corta, lanza un error que dice QUÉ VARIABLES fallan
    (solo sus nombres, nunca sus valores).
    """
    # Una variable vacía cuenta como faltante.
    faltan = [variable for variable in VARIABLES_CLAVE.values() if not entorno.get(variable)]
    if faltan:
        raise ErrorDatosEjemplo(
            "Faltan variables de entorno con las contraseñas de ejemplo: "
            + ", ".join(faltan)
            + ". Defínelas en tu terminal (no en un archivo) y vuelve a correr el script."
        )
    cortas = [
        variable
        for variable in VARIABLES_CLAVE.values()
        if len(entorno[variable]) < LARGO_MINIMO_CLAVE
    ]
    if cortas:
        raise ErrorDatosEjemplo(
            f"Estas contraseñas tienen menos de {LARGO_MINIMO_CLAVE} caracteres: "
            + ", ".join(cortas)
            + "."
        )
    return {cargo: entorno[variable] for cargo, variable in VARIABLES_CLAVE.items()}


def validar_base_local(url: URL) -> None:
    """Detiene el script si la base de datos no está en esta misma computadora."""
    # Además del host de la URL, se revisa el parámetro ?host= por si trae otro servidor.
    anfitriones = [url.host]
    extra = url.query.get("host")
    if extra:
        anfitriones += [extra] if isinstance(extra, str) else list(extra)
    # host None = conexión local por defecto (socket de la misma máquina).
    for anfitrion in anfitriones:
        if anfitrion is not None and anfitrion not in HOSTS_LOCALES:
            raise ErrorDatosEjemplo(
                "La base de datos configurada no es local. Por seguridad este script solo "
                "carga datos de ejemplo en un PostgreSQL de esta misma computadora "
                "(localhost). No se hizo nada."
            )


def _url_desde_entorno() -> URL:
    """URL de PostgreSQL tomada de DATABASE_URL (entorno o backend/.env)."""
    texto = obtener_url_base_datos()
    if not texto or not texto.startswith("postgresql"):
        raise ErrorDatosEjemplo(
            "No hay una DATABASE_URL de PostgreSQL. Defínela en el entorno o en backend/.env."
        )
    return make_url(texto)


# ---------------------------------------------------------------------------
# Ayudas para "buscar y, si no existe, crear" (así el script es repetible)
# ---------------------------------------------------------------------------


def _nuevo_resumen() -> dict[str, dict[str, int]]:
    """Contador por tabla: cuántas filas se crearon y cuántas ya existían."""
    return defaultdict(lambda: {"creados": 0, "existentes": 0})


def _obtener_o_crear(
    sesion: Session,
    resumen: dict[str, dict[str, int]],
    tabla: str,
    existente: object | None,
    crear: Callable[[], object],
):
    """Devuelve la fila que ya existe o, si no hay, crea una nueva con `crear()`.

    `crear` se pasa como función para que no se arme nada (por ejemplo un hash costoso)
    cuando la fila ya existía.
    """
    if existente is not None:
        resumen[tabla]["existentes"] += 1
        return existente
    nueva = crear()
    sesion.add(nueva)
    # flush envía el INSERT ya, para tener el id y que la base valide las reglas.
    sesion.flush()
    resumen[tabla]["creados"] += 1
    return nueva


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------


def _cargar_iglesias_y_sedes(
    sesion: Session, resumen: dict[str, dict[str, int]]
) -> dict[str, Iglesia]:
    """Crea las 4 iglesias y sus 5 sedes. Devuelve las iglesias por nombre."""
    iglesias: dict[str, Iglesia] = {}
    for datos in IGLESIAS:
        # El nombre de la iglesia es único en la base: es su "clave natural".
        iglesia = _obtener_o_crear(
            sesion,
            resumen,
            "iglesias",
            sesion.scalar(select(Iglesia).where(Iglesia.nombre == datos["nombre"])),
            lambda: Iglesia(nombre=datos["nombre"], pastor=datos["pastor"]),
        )
        iglesias[datos["nombre"]] = iglesia
        for nombre_sede in datos["sedes"]:
            # (iglesia, nombre) es único en `sedes`. Sin enlace de Maps: aún no lo tenemos.
            _obtener_o_crear(
                sesion,
                resumen,
                "sedes",
                sesion.scalar(
                    select(Sede).where(Sede.iglesia_id == iglesia.id, Sede.nombre == nombre_sede)
                ),
                lambda: Sede(iglesia_id=iglesia.id, nombre=nombre_sede, direccion=POR_CONFIRMAR),
            )
    return iglesias


def _cargar_miembros(
    sesion: Session, resumen: dict[str, dict[str, int]], iglesias: Mapping[str, Iglesia]
) -> dict[str, Miembro]:
    """Crea los miembros ficticios. Devuelve los miembros por nombre.

    Los miembros no tienen clave natural en la base, así que se reconocen por la pareja
    (iglesia, nombre): los nombres inventados no se repiten dentro de una iglesia.
    """
    miembros: dict[str, Miembro] = {}
    numero = 0  # contador para inventar teléfonos distintos (555-0101, 555-0102...)
    for nombre_iglesia, lista in MIEMBROS.items():
        iglesia = iglesias[nombre_iglesia]
        for nombre, estado, estado_civil, nacimiento, bautizo, ingreso in lista:
            numero += 1
            miembros[nombre] = _obtener_o_crear(
                sesion,
                resumen,
                "miembros",
                sesion.scalar(
                    select(Miembro).where(
                        Miembro.iglesia_id == iglesia.id, Miembro.nombre == nombre
                    )
                ),
                lambda: Miembro(
                    iglesia_id=iglesia.id,
                    nombre=nombre,
                    estado=estado,
                    estado_civil=estado_civil,
                    fecha_nacimiento=nacimiento,
                    fecha_bautizo=bautizo,
                    fecha_ingreso=ingreso,
                    # Teléfono con formato que no existe en la vida real.
                    telefono=f"555-{100 + numero:04d}",
                    correo=CORREOS.get(nombre),
                    direccion=POR_CONFIRMAR,
                ),
            )
    return miembros


def _cargar_cuentas(
    sesion: Session,
    resumen: dict[str, dict[str, int]],
    iglesias: Mapping[str, Iglesia],
    miembros: Mapping[str, Miembro],
    claves: Mapping[str, str],
) -> dict[str, Usuario]:
    """Crea las 6 cuentas de ejemplo (una por cargo). Devuelve las cuentas por cargo."""
    cuentas: dict[str, Usuario] = {}
    for cargo, nombre_usuario, nombre_completo, tiene_iglesia in CUENTAS:
        ficha = miembros.get(CUENTA_LIGADA.get(cargo, ""))
        cuentas[cargo] = _obtener_o_crear(
            sesion,
            resumen,
            "usuarios",
            # El nombre de usuario es único sin importar mayúsculas (índice sobre lower()).
            sesion.scalar(
                select(Usuario).where(func.lower(Usuario.nombre_usuario) == nombre_usuario.lower())
            ),
            # El hash (costoso a propósito) solo se calcula si la cuenta aún no existe.
            # Una cuenta que ya existe conserva su contraseña: no se le cambia.
            lambda: Usuario(
                nombre_usuario=nombre_usuario,
                contrasena_hash=crear_hash(claves[cargo]),
                nombre_completo=nombre_completo,
                cargo=cargo,
                iglesia_id=iglesias[IGLESIA_DEMO].id if tiene_iglesia else None,
                miembro_id=ficha.id if ficha is not None else None,
            ),
        )
    return cuentas


def _cargar_grupos(
    sesion: Session,
    resumen: dict[str, dict[str, int]],
    iglesias: Mapping[str, Iglesia],
    miembros: Mapping[str, Miembro],
) -> None:
    """Crea los grupos de la iglesia de la demo y a sus integrantes."""
    iglesia = iglesias[IGLESIA_DEMO]
    for tipo, nombre, lider, asistente in GRUPOS:
        # (iglesia, tipo, nombre) es único en `grupos`.
        grupo = _obtener_o_crear(
            sesion,
            resumen,
            "grupos",
            sesion.scalar(
                select(Grupo).where(
                    Grupo.iglesia_id == iglesia.id, Grupo.tipo == tipo, Grupo.nombre == nombre
                )
            ),
            lambda: Grupo(
                iglesia_id=iglesia.id,
                tipo=tipo,
                nombre=nombre,
                lider_miembro_id=miembros[lider].id,
                asistente_miembro_id=miembros[asistente].id if asistente else None,
            ),
        )
        # Integrantes: líder y asistente (si hay) más los que lista INTEGRANTES, solo en los
        # grupos que tienen lista (célula y ministerio); las redes y el área no la llevan.
        if nombre not in INTEGRANTES:
            continue
        for persona in dict.fromkeys([lider, asistente, *INTEGRANTES[nombre]]):
            if persona is None:
                continue
            _obtener_o_crear(
                sesion,
                resumen,
                "grupo_miembros",
                sesion.scalar(
                    select(GrupoMiembro).where(
                        GrupoMiembro.grupo_id == grupo.id,
                        GrupoMiembro.miembro_id == miembros[persona].id,
                    )
                ),
                # tipo_grupo es una copia del tipo del grupo; la base verifica que coincida.
                lambda: GrupoMiembro(
                    grupo_id=grupo.id, miembro_id=miembros[persona].id, tipo_grupo=grupo.tipo
                ),
            )


def cargar_datos(sesion: Session, claves: Mapping[str, str]) -> dict[str, dict[str, int]]:
    """Carga todos los datos de ejemplo con la sesión dada y devuelve el resumen.

    No confirma la transacción: eso lo decide quien llama (así las pruebas y el modo
    normal usan exactamente el mismo código). El ORDEN importa por las llaves foráneas:
    primero lo que otras tablas necesitan (iglesias), al final lo que depende de todo.
    """
    resumen = _nuevo_resumen()
    iglesias = _cargar_iglesias_y_sedes(sesion, resumen)
    miembros = _cargar_miembros(sesion, resumen, iglesias)
    # Las cuentas van después de los miembros: la del líder de célula apunta a su ficha.
    _cargar_cuentas(sesion, resumen, iglesias, miembros, claves)
    # Los grupos van al final: su líder y su asistente son miembros.
    _cargar_grupos(sesion, resumen, iglesias, miembros)
    return resumen


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------


def _cargar_en_base(url: URL, claves: Mapping[str, str]) -> dict[str, dict[str, int]]:
    """Abre la base, comprueba que esté migrada y carga todo en UNA sola transacción."""
    motor = create_engine(url)
    try:
        try:
            tablas = set(inspect(motor).get_table_names())
        except OperationalError:
            # Mensaje genérico a propósito: el error original podría traer datos de conexión.
            raise ErrorDatosEjemplo(
                "No se pudo conectar a la base de datos. Revisa que PostgreSQL esté "
                "corriendo y que DATABASE_URL sea correcta."
            ) from None
        faltan = sorted(TABLAS_REQUERIDAS - tablas)
        if faltan:
            raise ErrorDatosEjemplo(
                "Faltan tablas en la base (" + ", ".join(faltan) + "). Aplica primero las "
                "migraciones (alembic upgrade head); este script no las aplica."
            )
        # Todo o nada: si algo falla a la mitad, no queda ninguna fila a medias.
        with Session(motor) as sesion, sesion.begin():
            return cargar_datos(sesion, claves)
    finally:
        motor.dispose()


def _imprimir_resumen(resumen: Mapping[str, Mapping[str, int]]) -> None:
    """Muestra cuántas filas se crearon y cuántas ya existían (sin datos sensibles)."""
    print("Listo. Resumen por tabla:")
    for tabla, cuenta in resumen.items():
        print(f"  {tabla}: {cuenta['creados']} creadas, {cuenta['existentes']} ya existían")


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada. Devuelve 0 si todo salió bien y 1 si algo lo impidió."""
    analizador = argparse.ArgumentParser(description="Carga datos de ejemplo para la demo.")
    analizador.add_argument(
        "--confirmar",
        action="store_true",
        help="Sin esta bandera el script solo muestra la base destino y se detiene.",
    )
    argumentos = analizador.parse_args(argv)

    try:
        url = _url_desde_entorno()
        validar_base_local(url)
        # Se muestra solo el NOMBRE de la base; la URL puede llevar la contraseña.
        print(f"Base de datos destino: {url.database}")
        # Las contraseñas se validan ANTES de tocar la base.
        claves = leer_claves(os.environ)
        if not argumentos.confirmar:
            print("No se cargó nada. Para cargar los datos de ejemplo agrega --confirmar.")
            return 1
        resumen = _cargar_en_base(url, claves)
    except ErrorDatosEjemplo as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    _imprimir_resumen(resumen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
