# Registro de decisiones

Las decisiones están **propuestas** hasta que Marcos las marque como *confirmada*. Las respuestas de la clienta
(`docs/preguntas-cliente.md`) se resumen aquí.

| ID | Fecha | Decisión | Estado |
|---|---|---|---|
| D1 | 2026-10-28 | App **web** responsive (celular primero), no app móvil nativa. | propuesta |
| D2 | 2026-10-28 | Stack: FastAPI + SQLAlchemy + Alembic + PostgreSQL; React + Vite + Tailwind. Es el mismo que ya usó el equipo en TallerMoto, para no perder días aprendiendo. | propuesta |
| D3 | 2026-10-28 | Despliegue de demo: Render (API) + Vercel (web) + Neon (BD). | propuesta |
| D4 | 2026-10-28 | Roles iniciales: administrador general, pastor/administrador de sede, tesorero, líder de ministerio, secretario(a), miembro. Se ajustan con la entrevista. | propuesta |
| D5 | 2026-10-28 | Donaciones y gastos no se borran: se anulan con motivo. Datos financieros visibles solo para administrador, pastor de su sede y tesorero. | propuesta |
| D6 | 2026-10-28 | Calendario: Sprint 0 (28 oct), 1 (29–30 oct), 2 (31 oct–1 nov); 2 nov es solo entrega. Lo Deseable se recorta primero. | propuesta |
| D7 | 2026-10-28 | Solo datos inventados en repo y pruebas; nunca datos reales de miembros o donaciones. | propuesta |
| D8 | 2026-10-29 | La app es del Presbiterio de la 3ra IAFCJ: 4 iglesias (3ra de Mérida con 2 sedes, 4ta, 6ta y Huhí). Sin sede principal, pero rinden cuentas al pastor Jorge Lozano (presbítero). | confirmada (clienta) |
| D9 | 2026-10-29 | Dinero visible solo para pastor y tesorero de su iglesia; el presbítero lo ve en todas. Cada cargo ve solo su área. Reemplaza D4 y D5 en lo que contradigan. | confirmada (clienta) |
| D10 | 2026-10-29 | Ubicación = enlace de Google Maps (sin mapa propio). Horarios y ubicaciones consultables sin cuenta; el resto, solo liderazgo. | confirmada (clienta) |
| D11 | 2026-10-29 | Uso principal desde celular; también computadora. | confirmada (clienta) |
| D12 | 2026-10-29 | Cada pastor tiene un "apoyo" que usa la app por él. Sus permisos sobre el dinero están por confirmar. | pendiente |
| D13 | 2026-10-29 | Datos públicos de las iglesias pueden ser reales; personas y dinero de ejemplo, siempre ficticios. | propuesta |
| D14 | 2026-10-30 | Se registran los miembros (con fecha de ingreso) y sus 6 estados. Se guardan todos los datos propuestos salvo familia. | confirmada (clienta) |
| D15 | 2026-10-30 | Niños (4-11) y adolescentes (12-17) se registran con nombre, nacimiento, dirección y tutores. | confirmada (clienta) |
| D16 | 2026-10-30 | Asistencia: la marca el líder de célula; para quienes no tienen célula, el ujier (cargo rotativo) anota quién faltó. | confirmada (clienta) |
| D17 | 2026-10-30 | Ingresos por cantidades y tipo (diezmos, ofrendas, EVAMI, talento, otras con descripción); no se registra quién dio. Reemplaza el campo "miembro opcional" de donaciones. | confirmada (clienta) |
| D18 | 2026-10-30 | Gastos con lista fija de categorías; la tesorería está en sujeción al pastor local. Detalle de la autorización por confirmar. | confirmada / pendiente |
| D19 | 2026-11-02 | Nadie crea ni asigna un cargo con más acceso al dinero del que tiene: el apoyo del pastor solo crea cargos sin dinero; el pastor puede crear al tesorero de su iglesia; solo el presbítero crea pastores. Lo propuso Jessica; evita obtener el dinero por otra cuenta. | confirmada (Marcos) |
| D20 | 2026-11-03 | Reglas de permisos propuestas por Jessica (#10) y confirmadas por Marcos: (1) el "administrador" es el presbítero, sin rol técnico aparte; (2) el tesorero anula ingresos y gastos de su iglesia con motivo y registro, sin aprobación previa del pastor (provisional, pendiente de la clienta); (3) el tesorero no ve el listado de miembros; (4) solo el presbítero crea eventos y comunicados para todo el Presbiterio, pastor y apoyo solo para su iglesia; (5) pastor y apoyo no editan datos de otra iglesia; (6) el "secretario" de la clienta es el apoyo del pastor (provisional, pendiente de la clienta); (7) un presbítero no crea a otro desde la app; (8) nadie, salvo el presbítero, cambia su propio cargo. Crear y editar usuarios usan la misma validación de cargos. | confirmada (Marcos) / 2 y 6 provisionales |
