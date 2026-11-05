# Tessia

**Tessia** es una aplicación **web** (pensada para el celular) para el **Presbiterio de la 3ra IAFCJ**: cuatro iglesias de Mérida y Huhí, Yucatán (la 3ra de Mérida con dos sedes, Madero y Kanasín) que rinden cuentas al pastor Jorge Lozano, presbítero.
Permite llevar los horarios y ubicaciones de cada iglesia, los miembros, la asistencia, los eventos, los grupos, los comunicados y las finanzas (ingresos y gastos), con usuarios y permisos por cargo.

Proyecto escolar hecho con el método **Scrum** por un equipo de cuatro personas, con apoyo de agentes de IA (Claude Code y Codex) y un orquestador. Estado al **5 de noviembre de 2026**.

## Qué hace hoy

| Módulo | Qué se puede hacer |
|---|---|
| **Inicio de sesión y usuarios** | Entrar con usuario y contraseña; crear y editar usuarios con su cargo; cada cargo ve solo lo que le toca |
| **Iglesias y horarios** | Ficha de cada iglesia con sedes y redes; horarios por sede; **página pública** de horarios y ubicaciones (`/ubicaciones`, sin cuenta) |
| **Miembros** | Registro, búsqueda sin importar acentos y estados (activo, inactivo, visitante, en proceso de ganar, de discipular o de consolidar) |
| **Niños y adolescentes** | Registro con sus tutores y categoría calculada por edad |
| **Grupos y asignaciones** | Redes, células, ministerios, escuelas y áreas, con líder y asistente; asignar miembros (una sola célula por persona) |
| **Asistencia** | El líder de célula marca quién asistió y el ujier quién faltó, pensado para usarse con una mano en el celular |
| **Eventos y comunicados** | Crear, editar y consultar, por iglesia o para todo el Presbiterio; los comunicados tienen vigencia |
| **Ingresos y gastos** | Ingresos por culto y tipo (diezmos, ofrendas, EVAMI, talento y otras); gastos por categoría; **nada se borra, se anula con motivo**; solo los ven el pastor y el tesorero de su iglesia y el presbítero |

**Permisos:** el servidor valida el cargo de cada petición; ocultar un botón en la pantalla no basta. Las reglas están en [`docs/DECISIONES.md`](docs/DECISIONES.md) y el manual por cargo en [`docs/manual-usuario.md`](docs/manual-usuario.md).

## Pendiente o por hacer

Lo que **no** está terminado, dicho con claridad:

- **Reporte de célula:** falta el formato que la clienta usa hoy en sus listas físicas (decisión D34). El reporte financiero y el de asistencia ya están.
- **Dinero para otros cargos:** un botón para que el pastor dé acceso a las finanzas a otros cargos (decisión D22).
- **Dos cargos por persona** (hoy cada usuario tiene uno).
- **Foto del comprobante** en los gastos.
- **Eventos por tipo y cuota**, y avisos por **WhatsApp**.
- **Modo sin conexión:** no hay internet estable en todas las iglesias (por ejemplo, Huhí).
- **Despliegue en internet:** se decidió que la entrega es la aplicación funcionando y el repositorio; la guía para publicarla está en [`docs/despliegue.md`](docs/despliegue.md).

El detalle de las decisiones de la clienta está en [`docs/DECISIONES.md`](docs/DECISIONES.md) y sus respuestas en [`docs/preguntas-cliente.md`](docs/preguntas-cliente.md).

## Cómo correrla (demo en local)

Todo corre en una sola computadora. La guía paso a paso, con los comandos de PowerShell, las cuentas de ejemplo y qué hacer si algo falla, está en **[`docs/despliegue.md`](docs/despliegue.md)**, sección *Demo en local*. En resumen:

1. Tener **Python 3.12**, **Node.js** y **PostgreSQL** (las pruebas del equipo usan PostgreSQL 17).
2. Crear una base vacía, instalar el backend (`backend/`) y el frontend (`frontend/`).
3. Crear las tablas con `alembic upgrade head` y cargar los datos de ejemplo con `python -m scripts.cargar_datos_ejemplo --confirmar` (las contraseñas de las cuentas se eligen al correrlo; **no están en el repositorio**).
4. Arrancar la API (`python -m uvicorn app.main:app`) y la web (`npm run dev`, en `http://localhost:5173`).

Las cuentas de ejemplo son: `presbitero.ejemplo`, `pastor.ejemplo`, `apoyo.ejemplo`, `tesorero.ejemplo`, `lider.celula.ejemplo` y `ujier.ejemplo`.

## Cómo está hecha

| Parte | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, pytest, Ruff |
| Base de datos | PostgreSQL |
| Frontend | React, Vite, TypeScript, Tailwind, React Router |
| Integración continua | GitHub Actions: `ruff`, `pytest` con PostgreSQL, `npm run lint` y `npm run build` en cada pull request |

```
backend/app/modulos/   un módulo por tema: rutas, servicio, esquemas
backend/app/modelos/   tablas de la base de datos
backend/alembic/       migraciones
backend/tests/         pruebas (más de 800)
frontend/src/paginas/  una carpeta por módulo, con sus pantallas
docs/                  decisiones, manual de usuario, guía de demo y despliegue
```

Para probar el backend: desde `backend/`, `ruff check .` y `pytest` (necesita una `DATABASE_URL` de PostgreSQL). Para el frontend: desde `frontend/`, `npm run lint` y `npm run build`.

## Equipo

| Persona | GitHub | Rol Scrum | Rol técnico | IA |
|---|---|---|---|---|
| Marcos Ramos | NotCoffeeRS | Product Owner | Infraestructura, orquestador, merges | Claude Code |
| Vanessa Cuevas | aneley1234 | Scrum Master | Frontend | Claude Code |
| María de los Ángeles Cruz | angeles77734 | Developer | Lógica de negocio / backend | Codex |
| Jessica Fuentes | jessyfuentesguevara-png | Developer | Base de datos y pruebas | Claude Code |

## Cómo trabajamos

1. Todo trabajo sale de un **Issue**; el tablero es el proyecto "Iglesias" del perfil NotCoffeeRS.
2. Una rama por Issue: `tipo/<issue>-modulo-descripcion`. Nunca se hace push directo a `main`.
3. Pull request con `Closes #n`, la entrega del agente y las 4 casillas de revisión humana (plantilla incluida).
4. El orquestador verifica cada PR (`orquestador/verificacion`) y **Marcos hace el merge (squash)**.
5. Reglas completas para humanos y agentes: [`AGENTS.md`](AGENTS.md).

## Datos y privacidad

Los datos de iglesias son los públicos (nombre, pastor, horarios); **los miembros, las donaciones y los gastos del repositorio son ficticios**. Las contraseñas no se guardan en el repositorio ni en los Issues. La información de menores y de dinero solo la ven los cargos autorizados.
