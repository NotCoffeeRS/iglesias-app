# Pruebas manuales — Iglesias App

Lista de pruebas manuales y recorrido en el navegador para la entrega (Issue #35).

> **Cómo leer este documento.** Cada fila separa dos cosas que no deben mezclarse:
>
> - **Esperado según el código:** lo que se deduce de **leer el código** (menús, permisos, respuestas del servidor). **No es un resultado de prueba.**
> - **Resultado en el navegador:** lo que **Jessica vio** en su recorrido del 5 nov 2026, hecho en dos tandas (ver la sección 1). Lo que no se probó dice **"sin probar"**, y lo que no se pudo precisar dice **"POR CONFIRMAR"**.
>
> No se afirma ningún resultado que no haya sido observado. Las contraseñas de las cuentas **no están en este documento ni en el repositorio**.

## 1. Entorno probado

| Dato | Valor |
|---|---|
| Fecha del recorrido | 5 nov 2026 |
| Quién probó | Jessica (en el navegador, en su computadora) |
| Código, 1ª tanda | Rama `main`. La API se arrancó con el código de `main` en el commit **`b3bf76c`**. Después `main` solo avanzó con documentación (`23c1c7d` y `5e6a14f`): el backend y el frontend son los mismos |
| Código, 2ª tanda | Jessica hizo `git pull` de `5e6a14f` a **`c8793b9`** (el historial local del clon lo confirma), reinició a mano la API y la web y probó otra vez con las 6 cuentas. Este código ya trae el menú agrupado, "Mi cuenta" y los reportes financiero y de asistencia. Los resultados de la 2ª tanda están en la sección 3.8 |
| Base de datos | **`iglesias_demo`** en PostgreSQL 17 local, migraciones aplicadas hasta `0002` |
| API | `uvicorn` **sin** `--reload`, puerto 8000 |
| Web | `npm run dev`, puerto 5173 (`http://localhost:5173`) |
| Datos | Los de ejemplo del Issue #5 (ver la sección 5), más los 8 horarios que Jessica capturó durante el recorrido |

**Cuentas** (el usuario es público; las contraseñas las sabe solo quien armó la demo):

| Cargo | Usuario |
|---|---|
| Presbítero | `presbitero.ejemplo` |
| Pastor | `pastor.ejemplo` |
| Apoyo del pastor | `apoyo.ejemplo` |
| Tesorero | `tesorero.ejemplo` |
| Líder de célula | `lider.celula.ejemplo` |
| Ujier | `ujier.ejemplo` |

## 2. El recorrido del Issue #35 y su estado

El Issue pide: **login, iglesia, miembro, ingreso, gasto y reporte**.

| Paso | Estado | Qué se probó |
|---|---|---|
| Login | **Probado** | Las 6 cuentas inician sesión |
| Iglesia | **Parcial** | Horarios y ubicaciones sí (ver la sección 4). La ficha y la lista de Iglesias: **sin probar** |
| Miembro | **Parcial** | El formulario `/miembros/nuevo` abre con el tesorero y con el líder de célula (no se guardó nada). Registrar y consultar la lista de miembros: **sin probar** |
| Ingreso | **Parcial** | Se consultan con el tesorero, con el presbítero y con una cuenta que fue el pastor o el tesorero (POR CONFIRMAR; ver la sección 3). Registrar y anular: **sin probar** |
| Gasto | **Parcial** | Igual que ingresos: se consultan; registrar y anular: **sin probar** |
| Reporte | **Parcial** | En la 1ª tanda el reporte financiero (#29) todavía no existía. En la 2ª (`c8793b9`) se **vio** el reporte financiero con presbítero, pastor y tesorero, y el de asistencia con el pastor y el ujier. Los totales y el detalle por cuenta: **POR CONFIRMAR** (ver la sección 3.8) |

## 3. Matriz cuenta × módulo

Los menús "esperados" salen de las reglas del código del frontend (`frontend/src/componentes/cargos.ts` y el `rutas.tsx` de cada módulo). El **servidor vuelve a validar todo**: el menú solo decide qué se muestra.

Los datos "esperados" del mes salen de los datos de ejemplo: el 1 de nov hay ingresos de $9,400.00 en la 3ra, $2,860.50 en la 4ta y $1,075.00 en la 6ta (total $13,335.50), y un gasto de $780.00 en la 3ra.

### 3.1 Todas las cuentas

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Inicio de sesión | Cada cuenta entra con su usuario y contraseña | **Las 6 cuentas inician sesión** |

### 3.2 Presbítero (`presbitero.ejemplo`)

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Menú | Inicio, Iglesias, Horarios, Miembros, Grupos, Asignaciones, Niños y adolescentes, Usuarios, Ingresos, Gastos, Reporte financiero, Eventos, Comunicados (sin Asistencia) | **POR CONFIRMAR** (ver la nota de abajo) |
| Ingresos | Las 4 iglesias, con selector "Todas las iglesias". Este mes (1 al 5 de nov): $13,335.50 | Ve las 4 iglesias (selector "Todas las iglesias"). **$13,335.50 este mes** |
| Gastos | Las 4 iglesias, con selector. Este mes: $780.00 | Selector "Todas las iglesias". **$780.00 este mes** |
| Niños y adolescentes (`/menores`) | Lista vacía (los datos de ejemplo no traen menores) y el botón "Registrar menor" | **Lista vacía con "Registrar menor"** |
| Asignaciones | Los 6 grupos de la 3ra | **POR CONFIRMAR** (ver la nota de abajo) |
| Miembros, Grupos, Usuarios, Iglesias, Eventos, Comunicados | Visibles en el menú | Sin probar |
| Reporte financiero | En la 1ª tanda (`b3bf76c`) la API no existía todavía (#29); ya existe | Sin probar en la 1ª tanda. 2ª tanda: ver la sección 3.8 |

> **Nota (POR CONFIRMAR).** Se vio una cuenta con **menú completo** y **Asignaciones con los 6 grupos de la 3ra**. Pudo ser el presbítero o el pastor; no se distinguió cuál era. Por eso esas dos filas del presbítero y las del pastor quedan por confirmar.

### 3.3 Pastor (`pastor.ejemplo`)

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Menú | El mismo del presbítero | **POR CONFIRMAR** (ver la nota de la sección 3.2) |
| Ingresos y Gastos | Solo la 3ra, sin selector. Este mes: $9,400.00 de ingresos y $780.00 de gastos | Una cuenta con Ingresos y Gastos mostró **solo la 3ra, $9,400 y $780 este mes**. **POR CONFIRMAR** si fue el pastor o el tesorero |
| Asignaciones | Los 6 grupos de la 3ra | **POR CONFIRMAR** (ver la nota de la sección 3.2) |
| Niños y adolescentes, Miembros, Grupos, Usuarios, Eventos, Comunicados | Visibles en el menú | Sin probar |

### 3.4 Apoyo del pastor (`apoyo.ejemplo`)

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Menú | Inicio, Iglesias, Horarios, Miembros, Grupos, Asignaciones, Niños y adolescentes, Usuarios, Eventos, Comunicados. Sin Ingresos, Gastos, Reporte financiero ni Asistencia | Tiene **Niños y adolescentes, Usuarios y Asignaciones**, y **sin Ingresos ni Gastos**. El resto del menú: sin anotar |
| Asignaciones | Elige un grupo y ve sus integrantes (los 6 grupos de la 3ra) | **Selector de grupos vacío hasta elegir** |
| Ingresos y Gastos por dirección | El servidor responde 403 (D22: sin acceso al dinero por defecto) | Sin probar |

### 3.5 Tesorero (`tesorero.ejemplo`)

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Menú | Inicio, Iglesias, Horarios, Ingresos, Gastos, Reporte financiero, Eventos, Comunicados | **Coincide:** Inicio, Iglesias, Horarios, Ingresos, Gastos, Reporte financiero, Eventos, Comunicados |
| Ingresos | Sin selector, solo la 3ra (18 ingresos de ejemplo en octubre y noviembre) | **Sin selector, solo la 3ra, 18 ingresos** |
| Gastos | Solo la 3ra | **Solo la 3ra** |
| `/usuarios/nuevo` | No puede crear usuarios (el servidor le responde 403) | **"Tu cargo no administra usuarios"** |
| `/miembros/nuevo` | El formulario abre (la web solo oculta el menú, no bloquea la dirección); el 403 llega al guardar | **El formulario abre** (no se guardó nada; el 403 al guardar: sin probar) |
| `/menores` | "Sin acceso" | **"Sin acceso"** |
| Asignaciones | No aparece en el menú | **Sin Asignaciones en el menú** |
| Reporte financiero | En la 1ª tanda (`b3bf76c`) la API no existía todavía (#29); ya existe | Sin probar en la 1ª tanda. 2ª tanda: ver la sección 3.8 |

### 3.6 Líder de célula (`lider.celula.ejemplo`)

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Menú | Inicio, Asistencia, Iglesias, Horarios, Miembros, Grupos, Asignaciones, Eventos, Comunicados. Sin Ingresos, Gastos ni Usuarios | **Coincide:** Inicio, Asistencia, Iglesias, Horarios, Miembros, Grupos, Asignaciones, Eventos, Comunicados (sin Ingresos, Gastos ni Usuarios) |
| Asistencia | Su célula (Célula Betania) con sus 6 miembros | **Célula Betania con 6 miembros** |
| `/usuarios/nuevo` | No puede crear usuarios (el servidor le responde 403) | **"Tu cargo no administra usuarios"** |
| Formularios de crear (miembros, grupos, eventos y comunicados) | Abren; el 403 llega al guardar | **Abren los 4 formularios** (no se guardó nada; el 403 al guardar: sin probar) |
| Asignaciones | Célula Betania con 6 integrantes. Puede quitar integrantes de su grupo, pero no agregar (posible P-1, ver PR #99) | **Célula Betania con 6 integrantes y botón "Quitar" en cada uno** (no se pulsó) |
| `/menores` | "Sin acceso" | **"Sin acceso"** |

### 3.7 Ujier (`ujier.ejemplo`)

| Módulo | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Menú | Inicio, Asistencia, Iglesias, Horarios, Eventos, Comunicados. Sin Asignaciones | **Coincide:** Inicio, Asistencia, Iglesias, Horarios, Eventos, Comunicados. **Sin Asignaciones** |
| Asistencia | La lista de los miembros sin célula de su iglesia, para marcar quién faltó | Sin probar |

### 3.8 Segunda tanda: menú agrupado, "Mi cuenta" y reportes (código `c8793b9`)

Jessica volvió a entrar con las 6 cuentas después de actualizar el código (ver la sección 1). Aquí van **solo sus observaciones**, con las palabras que usó. Lo que no dijo queda como **POR CONFIRMAR** o **sin probar**; no se completó nada por deducción.

Lo "esperado" sale de leer el código: el menú se agrupa en Iglesia, Personas y Dinero; el reporte financiero lo ven presbítero, pastor y tesorero (el servidor le responde 403 a los demás), y el presbítero, si no elige una iglesia, recibe además un consolidado; el reporte de asistencia lo ven todos los cargos menos el tesorero, con alcance por cargo (el presbítero, todas las iglesias; pastor y apoyo, su iglesia; el ujier, los miembros sin célula de su iglesia; el líder de célula, los integrantes de los grupos que dirige).

| Cuenta | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Presbítero | Reporte financiero con las 4 iglesias y consolidado. Menú agrupado. "Mi cuenta" en el menú | **Reporte financiero con las 4 iglesias; menú agrupado; "Mi cuenta" (perfil) visible.** Si apareció el consolidado y los totales: **POR CONFIRMAR**. Reporte de asistencia: **sin probar** |
| Pastor | Reporte financiero y de asistencia, solo de su iglesia (la 3ra). Sin consolidado | **Ve el reporte financiero y el de asistencia; el menú y "Mi cuenta" se ven bien.** Qué iglesias salieron y los totales: **POR CONFIRMAR** |
| Tesorero | Reporte financiero solo de su iglesia. Sin reporte de asistencia | **Se ve el reporte financiero; el menú y "Mi cuenta" se ven bien.** Qué iglesias salieron y los totales: **POR CONFIRMAR**. Si le aparece el reporte de asistencia: **sin probar** |
| Apoyo del pastor | Sin reporte financiero. Con reporte de asistencia de su iglesia | **No tiene reporte financiero; lo demás normal.** Si le aparece el reporte de asistencia: **POR CONFIRMAR** |
| Líder de célula | Sin reporte financiero. Reporte de asistencia solo con los integrantes de los grupos que dirige | **"Cuenta con lo acordado, se ve bien".** Qué módulos y reportes ve exactamente: **POR CONFIRMAR** |
| Ujier | Sin reporte financiero. Reporte de asistencia con los miembros sin célula de su iglesia | **Aparece el reporte de asistencia.** Qué datos muestra: **POR CONFIRMAR** |

Siguen **sin probar** en la 2ª tanda: el cierre de sesión desde "Mi cuenta", y si el consolidado del reporte financiero apareció solo para el presbítero.

## 4. Horarios y ubicaciones

| Prueba | Esperado según el código | Resultado en el navegador |
|---|---|---|
| Capturar horarios | Los horarios conocidos suman 8 (D31: 3ra Madero y Kanasín, 4ta, Huhí con 3, 6ta con 2) | **Jessica capturó 8 horarios** |
| Horario de Kanasín | Domingos 11:30 (D31) | **Lo corrigió a 11:30 a. m.** |
| `/ubicaciones` | Las 5 ubicaciones (4 iglesias, la 3ra con 2 sedes). Es pública: se ve sin iniciar sesión | **Muestra las 5 ubicaciones** (no se anotó si fue con o sin sesión iniciada) |
| Direcciones | "Por confirmar" (aún no se tienen las reales) | **Dicen "Por confirmar"** |

## 5. Datos de ejemplo cargados

Cargados con `backend/scripts/cargar_datos_ejemplo.py` (Issue #5). El script no carga horarios, direcciones reales, enlaces de Maps, redes ni fotos.

| Dato | Cantidad |
|---|---|
| Iglesias | 4 (la 3ra de Mérida con 2 sedes: Madero y Kanasín) |
| Sedes | 5 |
| Miembros | 22 |
| Grupos | 6 |
| Cuentas | 6 (una por cargo) |
| Ingresos | 27 |
| Gastos | 12 (1 ya anulado) |
| Menores, eventos y comunicados | 0 (salen vacíos) |

## 6. Sin sesión y CORS

| Prueba | Resultado en el navegador |
|---|---|
| Entrar a una pantalla protegida sin iniciar sesión | Sin probar |
| Que la web hable con la API (CORS) | No se probó por separado. Las pantallas que mostraron datos (por ejemplo Ingresos o Asistencia) los pidieron a la API, lo que indica que el CORS funcionaba (deducción, no una prueba directa) |

**Comprobaciones aparte** (las hizo Claude Code con peticiones directas a la API, **no en el navegador y no son parte del recorrido de Jessica**):

- `GET /salud` responde 200.
- Con el origen `http://localhost:5173`, tanto `GET /salud` como la petición previa del navegador (`OPTIONS /auth/login`) devuelven `access-control-allow-origin: http://localhost:5173`.
- Sin sesión, `/ingresos`, `/gastos`, `/menores` y `/asignaciones/grupos` responden **401**.
- Sin sesión, `/publico/iglesias` (horarios y ubicaciones) responde 200.

Los casos de sesión (sin sesión, token vencido o alterado, credenciales incorrectas y cuenta desactivada) están cubiertos por pruebas automáticas en el **PR #99** (`backend/tests/test_permisos.py`), pendiente de fusión al escribir esto.

## 7. Pendientes

| Pendiente | Detalle |
|---|---|
| **Reporte financiero** (#29) | No existe la API; el paso "reporte" del recorrido no se pudo probar. Lo tomó Ángeles |
| **Reporte de asistencia** (#31) | No existe todavía. Lo tomó Ángeles |
| **`backend/tests/test_recorrido.py`** | La prueba automática del recorrido (la otra mitad del Issue #35) **no se hizo todavía** |
| Registrar y anular ingresos y gastos en el navegador | Sin probar |
| Registrar miembros, menores, eventos y comunicados | Sin probar (solo se abrió el formulario en algunas cuentas) |
| Quitar un integrante desde Asignaciones | Sin probar (el botón estaba visible) |
| Asistencia del líder de célula y del ujier (marcar y guardar) | Sin probar |
| Cuentas por confirmar | Cuál fue el presbítero y cuál el pastor (ver la sección 3.2), y si "Ingresos y Gastos con $9,400 y $780" fue el pastor o el tesorero (sección 3.3) |

## 8. Fallos encontrados

El criterio del Issue pide reportar los fallos como Issues `bug`.

| Fallo | Dónde | Estado |
|---|---|---|
| El texto **"Comunicados"** se sale de su tarjeta en la pantalla de Inicio | Inicio (detalle visual), visto con el ujier y con el líder de célula | Jessica se lo pasó a Marcos y él a Vanessa. **No hay todavía un Issue `bug` abierto** por esto |

Issues `bug` ya registrados y **cerrados** al escribir esto: #82, #83, #84 y #85.

## 9. Notas para después

- **(a) La web solo oculta módulos en el menú; no bloquea las direcciones.** *Observado:* el tesorero abre el formulario de `/miembros/nuevo`, y el líder de célula abre los formularios de miembros, grupos, eventos y comunicados. *Sin probar:* que el 403 llegue recién al guardar; eso **se deduce del código** (el servidor sí valida todo). Una pantalla de "sin permiso" desde el principio sería una mejora.
- **(b) 10 avisos de seguridad de nivel moderado** al correr `npm install` en `frontend`. No se corrigieron (no se ejecutó `npm audit fix`, que podría cambiar versiones y el `package-lock.json`); decidir después de la demo.
- **(c) Reiniciar la API a mano después de cada `git pull`.** En Windows el recargado automático (`--reload`) se queda a medias y el CORS deja de funcionar hasta reiniciar (ver `docs/despliegue.md`).
