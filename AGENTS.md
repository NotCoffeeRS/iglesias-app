# AGENTS.md — Reglas para todos los agentes de IA

Este archivo es la **fuente única de reglas** para cualquier agente que trabaje en este repositorio,
sea Codex (lo lee automáticamente) o Claude Code (lo importa desde `CLAUDE.md`).
Si algo de aquí contradice una instrucción informal, **gana este archivo**.

## 1. Contexto del proyecto

**Iglesias App**: aplicación **web** (sobre todo en celular) del **Presbiterio de la 3ra IAFCJ**: 4 iglesias
(3ra de Mérida con 2 sedes, Madero y Kanasín; 4ta y 6ta de Mérida; Huhí, Yucatán) que rinden cuentas al pastor Jorge Lozano (presbítero).
Horarios y ubicaciones, usuarios y cargos, miembros, asistencia, eventos, grupos (redes, células, ministerios), donaciones y aportaciones,
gastos y costos, comunicados y reportes. Uso interno del liderazgo; solo horarios y ubicaciones son públicos. Proyecto escolar con método Scrum; entrega el 2 de noviembre de 2026
(meta interna: 1 de noviembre).

Idioma: **español** en la interfaz, los mensajes de commit, los Issues y la documentación.
El código (variables, funciones, tablas) puede ir en español sin acentos.
La interfaz debe ser **responsive**: se usará mucho desde el celular.

## 2. Stack (propuesto, ver `docs/DECISIONES.md`)

| Parte | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, pytest, Ruff |
| Base de datos | PostgreSQL (dinero `NUMERIC(12,2)`, fechas con zona horaria `America/Merida`) |
| Frontend | React + Vite, Tailwind, ESLint + Prettier |
| Despliegue | Render (API) + Vercel (web) + Neon (base de datos) |

## 3. Estructura

```
backend/app/        API FastAPI: modelos, rutas, lógica de negocio
backend/alembic/    migraciones de base de datos
backend/tests/      pruebas con pytest
frontend/src/       pantallas y componentes React
docs/               documentación y registro de decisiones
```

## 4. Reglas obligatorias (no negociables)

1. **Trabaja solo sobre un Issue.** Tu tarea es exactamente lo que dice el Issue que te pasó tu humano.
2. **Toca solo los archivos autorizados** en el Issue. Si necesitas otro, **detente y pregúntalo**.
3. **No inventes requisitos ni datos.** Si falta información o algo es contradictorio, repórtalo como duda y marca la tarea como bloqueada.
4. **No amplíes el alcance.** Si ves una mejora útil, escríbela como sugerencia; no la implementes.
5. **Nunca** hagas `git push` a `main`, merge de pull requests, force push ni borres ramas ajenas.
   La aprobación y el merge son exclusivamente humanos.
6. **Nunca** subas secretos: contraseñas, tokens, cadenas de conexión ni archivos `.env`.
   Usa variables de entorno y documenta el nombre en `.env.example`.
7. **Cambios de esquema de base de datos** solo mediante migraciones de Alembic y solo en tareas del perfil Datos/QA.
   Nunca modifiques la base de datos a mano.
8. **Toda lógica nueva lleva pruebas.** En módulos críticos (donaciones, gastos, reporte financiero, usuarios y permisos,
   migraciones) las pruebas son obligatorias y deben cubrir el caso del Issue.
9. **Privacidad:** los datos públicos de las iglesias (nombre, dirección, pastor, redes) pueden ser reales; miembros,
   teléfonos personales, donaciones y gastos de ejemplo son **siempre ficticios**. Nunca datos reales de personas ni de dinero en el repo, Issues o capturas. Las contraseñas se guardan con hash; nunca en texto plano.
   Sin datos personales en URLs.
10. **Permisos en el servidor:** el backend valida el rol de cada petición; ocultar un botón en la interfaz no basta.
11. Antes de entregar, **corre las pruebas y el linter** y reporta el resultado real (no lo supongas).

## 5. Formato obligatorio de entrega

Al terminar, responde **exactamente** con esta estructura (se copia en la descripción del pull request):

```markdown
## Entrega del agente
- **Issue:** #<número> · **Historia:** HU-<xx>
- **Objetivo atendido:** <copiado del Issue>
- **Archivos creados o modificados:**
  - `ruta/archivo` — qué cambió
- **Resumen de cambios:** <qué hiciste y por qué>
- **Requisitos que atiende:** <funcionalidad>
- **Pruebas realizadas y resultados:** <comando ejecutado y resultado real, o "faltan por ejecutar: …">
- **Problemas conocidos o limitaciones:** <o "ninguno">
- **Dudas o decisiones pendientes para un humano:** <o "ninguna">
```

Una entrega sin alguno de estos campos se devuelve antes de revisarse.

## 6. Perfiles de agente

Cada tarea indica el perfil (etiqueta `agente:*` del Issue). Respeta sus límites:

| Perfil | Lo dirige | Puede modificar | No puede modificar |
|---|---|---|---|
| **Analista** | Vanessa | `docs/`, borradores de historias y criterios | El backlog priorizado final (lo aprueba Marcos) |
| **Interfaz** | Vanessa | `frontend/src/` (componentes, estilos, formularios) | Lógica de negocio del backend, esquema de base de datos |
| **Backend** | Angeles (Codex) | `backend/app/` en los archivos del Issue | Esquema de base de datos (se pide a Jessica con un Issue), `frontend/` |
| **Datos/QA** | Jessica | `backend/alembic/`, `backend/tests/` | Aplicar migraciones directamente a la base de demo |

## 7. Convenciones

- **Rama:** `tipo/<número-de-issue>-modulo-descripcion` → ej. `feature/23-miembros-registro`.
  Tipos: `feature`, `fix`, `docs`, `test`, `chore`.
- **Commit:** `tipo(modulo): descripción en presente (#issue)` → ej. `feat(miembros): registra miembro nuevo (#23)`.
- **Pull request:** título claro, `Closes #<número>` en la descripción y la entrega del punto 5.
- El merge es **squash** y lo hace Marcos, solo con la CI y la verificación del orquestador
  (`orquestador/verificacion`) en verde.

## 8. Cómo correr pruebas y linters

```bash
# Backend (cuando exista backend/pyproject.toml)
cd backend
ruff check .
pytest

# Frontend (cuando exista frontend/package.json)
cd frontend
npm run lint
npm run build
```

## 9. Reglas de negocio (respuestas de la clienta, 29 oct; lo marcado (?) sigue pendiente)

- El **Presbiterio** tiene 4 iglesias. La 3ra de Mérida tiene **2 sedes**; las demás, una. Cada iglesia: nombre, foto de fachada,
  dirección y enlace de Google Maps, pastor, teléfono del pastor y de la iglesia (opcionales), redes sociales propias y relacionadas (varias).
- **Horarios** por sede y tipo de servicio: culto de domingo, culto entre semana, oración, jóvenes, DNA, escuela (IBID), célula, ministerio.
- **Grupos**: redes (varones, damas, jóvenes), células, ministerios, escuelas y áreas (p. ej. la tiendita); cada uno con líder y asistente/segundo.
- **Cargos**: presbítero, pastor, esposa de pastor, apoyo del pastor, tesorero, líder de red/célula/ministerio, asistente, diácono, ministro, encargado de área.
- **Visibilidad**: cada cargo ve solo lo de su área; el pastor ve todo lo de su iglesia; el presbítero ve todo el Presbiterio.
- **Dinero**: solo pastor y tesorero de su iglesia lo ven, y el presbítero en todas las iglesias. Apoyo del pastor y demás cargos: sin acceso (?).
- Horarios y ubicaciones son **públicos** (sin cuenta); todo lo demás exige sesión.
- Donaciones y gastos **no se borran**: se anulan con motivo (?). Reporte financiero: donaciones − gastos por iglesia y periodo, sin anulados; el presbítero ve el consolidado.
- **Miembros**: nombre, teléfono, correo, nacimiento, dirección, estado civil, fecha de bautizo y fecha desde que forman parte de la congregación (sin datos de familia).
  Estados: activo, inactivo, visitante, en proceso de ganar, de discipular o de consolidar.
- **Niños y adolescentes**: nombre, nacimiento, dirección, niño/niña (4 a 11 años) o adolescente (12 a 17) y sus tutores.
- **Asistencia**: el líder de célula marca quién de su célula asistió; el ujier (cargo rotativo) marca quién faltó de quienes no tienen célula.
- **Ingresos**: se registran **cantidades** por culto o fecha y por tipo (diezmos, ofrendas, EVAMI, talento/venta de comida, otras donaciones con descripción). No se registra quién dio.
- **Gastos**: categorías luz, agua, renta, mantenimiento, material de construcción, materiales y reposiciones, apoyo a miembros, otros. Tesorería actúa en sujeción al pastor local (flujo de autorización por confirmar (?)).

