"""Listas cerradas de valores permitidos (Issue #4).

Cada lista se escribe UNA sola vez aquí y los modelos la usan en sus CHECK. Las claves
(el texto de cada valor) son las mismas que ya usa el frontend, para que nadie tenga
que traducirlas. Si hay que agregar un valor, se hace con una migración nueva que
cambie el CHECK correspondiente.
"""

# Tipos de servicio (8): horarios e ingresos por culto (Issues #4 y #14).
TIPOS_SERVICIO = (
    "culto_domingo",
    "culto_entre_semana",
    "oracion",
    "jovenes",
    "dna",
    "escuela_ibid",
    "celula",
    "ministerio",
)

# Servicios de una asistencia: los 8 de arriba MÁS "otro". La decisión D16 dice que el
# líder marca la asistencia al culto "domingo, miércoles u otro día", y la pantalla de
# asistencia (PR #47) ya usa "otro". Horarios e ingresos siguen con los 8 (Issue #4).
TIPOS_SERVICIO_ASISTENCIA = TIPOS_SERVICIO + ("otro",)

# Días de la semana de un horario (la lista la propone el frontend, Issue #15).
DIAS_SEMANA = (
    "domingo",
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
)

# Redes sociales de una iglesia: propias o relacionadas (Issue #12).
TIPOS_RED_SOCIAL = ("propia", "relacionada")

# Estados de un miembro (6): Issue #4 y decisión D14.
ESTADOS_MIEMBRO = (
    "activo",
    "inactivo",
    "visitante",
    "en_proceso_ganar",
    "en_proceso_discipular",
    "en_proceso_consolidar",
)

# Estado civil (la lista la propone el frontend, Issue #18; pendiente de confirmar).
ESTADOS_CIVILES = ("soltero", "casado", "union_libre", "divorciado", "viudo")

# Sexo de un menor: la categoría niño/niña/adolescente depende de él (Issue #19).
SEXOS = ("femenino", "masculino")

# Tipos de grupo (5): Issues #4 y #20.
TIPOS_GRUPO = ("red", "celula", "ministerio", "escuela", "area")

# Tipos de ingreso (5): Issues #4 y #25, decisión D17.
TIPOS_INGRESO = ("diezmos", "ofrendas", "evami", "talento", "otras")

# Categorías de gasto (8): Issues #4 y #27.
CATEGORIAS_GASTO = (
    "luz",
    "agua",
    "renta",
    "mantenimiento",
    "material_construccion",
    "materiales_reposiciones",
    "apoyo_miembros",
    "otros",
)
