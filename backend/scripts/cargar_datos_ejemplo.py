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

from sqlalchemy import inspect, select
from sqlalchemy.engine import URL, create_engine, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.modelos import Iglesia, Sede
from app.modelos.utilidades import obtener_url_base_datos

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
            lambda datos=datos: Iglesia(nombre=datos["nombre"], pastor=datos["pastor"]),
        )
        iglesias[datos["nombre"]] = iglesia
        for nombre_sede in datos["sedes"]:
            # (iglesia, nombre) es único en `sedes`. Sin enlace de Maps: aún no lo tenemos.
            _obtener_o_crear(
                sesion,
                resumen,
                "sedes",
                sesion.scalar(
                    select(Sede).where(
                        Sede.iglesia_id == iglesia.id, Sede.nombre == nombre_sede
                    )
                ),
                lambda iglesia=iglesia, nombre_sede=nombre_sede: Sede(
                    iglesia_id=iglesia.id, nombre=nombre_sede, direccion=POR_CONFIRMAR
                ),
            )
    return iglesias


def cargar_datos(sesion: Session, claves: Mapping[str, str]) -> dict[str, dict[str, int]]:
    """Carga todos los datos de ejemplo con la sesión dada y devuelve el resumen.

    No confirma la transacción: eso lo decide quien llama (así las pruebas y el modo
    normal usan exactamente el mismo código).
    """
    resumen = _nuevo_resumen()
    _cargar_iglesias_y_sedes(sesion, resumen)
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
