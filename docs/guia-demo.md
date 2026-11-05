# Guía de demo — Iglesias App

Guion para presentar la aplicación en unos **15 minutos**, mostrando lo que hace cada cargo. Está pensado para hacerse en un
**celular** (o en una ventana angosta de la computadora), porque así se usará.

> **Datos y claves.** Todo es de ejemplo: nombres, teléfonos, montos y miembros son inventados. **Las contraseñas de las cuentas de ejemplo
> no están en el repositorio**: se las pasa Jessica o Marcos por otro medio. No muestres contraseñas en pantalla ni tomes capturas con datos reales.

## 1. Antes de empezar (lista de revisión)

Marca cada punto antes de presentar. Si uno falla, mira la sección 5.

- [ ] **La API está desplegada** y responde (T-07, Issue #34). Sin ella, todas las pantallas dicen "No se pudo conectar".
- [ ] **La web puede hablar con la API** (CORS configurado en el servidor). Sin eso el navegador bloquea las peticiones.
- [ ] **Hay datos de ejemplo** cargados (T-06, Issue #5): las 4 iglesias, la 3ra de Mérida con 2 sedes, horarios, miembros, algunos grupos,
  y ingresos y gastos de uno o dos cultos.
- [ ] **Hay una cuenta de ejemplo por cargo**: presbítero, pastor, apoyo del pastor, tesorero, líder de célula y ujier.
- [ ] La sesión está **cerrada** en el navegador y probaste la dirección de la app desde el celular.
- [ ] El celular tiene **internet** y la pantalla no se apaga sola.

> **Truco:** abre cada cargo en una **ventana privada distinta**, así no cierras y abres sesión cada vez.

> **Estado al 3 nov 2026:** la API real todavía no está lista (solo existe `/salud`), por lo que esta guía **no se puede seguir completa
> hoy**. Las pantallas ya están construidas y probadas con respuestas simuladas.

## 2. Guion

| # | Min | Quién | Qué se muestra |
|---|---|---|---|
| 1 | 2 | Sin cuenta | Horarios y cómo llegar |
| 2 | 2 | Presbítero | Inicio y ficha de una iglesia |
| 3 | 2 | Pastor | Cambiar un horario |
| 4 | 3 | Apoyo y pastor | Crear usuarios con límites |
| 5 | 3 | Tesorero | Ingresos, gastos y anular |
| 6 | 2 | Presbítero | Reporte financiero |
| 7 | 2 | Líder de célula y ujier | Asistencia en el celular |
| 8 | 1 | Cualquiera | Miembros y grupos |

### 1. Sin cuenta: horarios y ubicaciones (2 min)

1. Abre `/ubicaciones` sin iniciar sesión.
2. **Di:** "Esto es lo único público: cualquiera puede ver cuándo nos reunimos y cómo llegar."
3. Toca **Cómo llegar** en una sede: abre Google Maps. Toca el teléfono de la iglesia: se marca.
4. **Muestra:** que no hay miembros, dinero ni teléfonos personales.

### 2. Presbítero: Inicio y ficha de la iglesia (2 min)

1. Toca **Iniciar sesión** y entra como **presbítero**.
2. **Muestra Inicio:** el mosaico con los accesos. **Di:** "El presbítero ve todo el Presbiterio."
3. Menú → **Iglesias** → la **3ra de Mérida**: foto, pastor, redes sociales y **2 sedes** con su enlace de Google Maps.
4. Toca **Editar ficha** y regresa sin cambiar nada: se ve que se pueden agregar sedes y redes.

### 3. Pastor: cambiar un horario (2 min)

1. Entra como **pastor** (ventana privada).
2. Menú → **Horarios** → **Agregar horario**: elige, por ejemplo, **Oración**, un día y una hora. Toca **Agregar horario**.
3. Abre `/ubicaciones` en otra pestaña: el horario nuevo **ya aparece**.
4. **Di:** "Una sede puede tener varios horarios del mismo tipo: culto de domingo, entre semana, oración, jóvenes, DNA, escuela, célula o ministerio."

### 4. Apoyo y pastor: crear usuarios con límites (3 min)

1. Entra como **apoyo del pastor**. Menú → **Usuarios** → **Crear usuario**.
2. Abre la lista de **Cargo**. **Muestra:** no aparecen **Pastor** ni **Tesorero**.
3. **Di:** "El apoyo no puede dar acceso al dinero, ni a un tesorero: así nadie obtiene el dinero por otra cuenta."
4. Entra como **pastor** y abre la misma lista. **Muestra:** ahora sí aparece **Tesorero**, pero no **Pastor** (solo el presbítero crea pastores).
5. Crea un usuario de ejemplo con cargo **Líder de célula** y confirma que aparece en la lista. **No muestres la contraseña.**

### 5. Tesorero: ingresos, gastos y anular (3 min)

1. Entra como **tesorero**. Menú → **Ingresos** → **Registrar ingresos**.
2. Elige el culto del **domingo** y captura: diezmos, ofrendas, **EVAMI**, talento y "otras" (con su descripción). Mira cómo sube el **total**.
3. **Di:** "Aquí no se anota quién dio, solo la cantidad." Toca **Registrar**.
4. Menú → **Gastos** → **Registrar gasto**: categoría **Luz**, un monto y una nota.
5. En la lista toca **Anular** en un gasto: escribe el motivo. **Muestra:** queda tachado, con su motivo, y **el total baja**. **Di:** "Nada se borra."
6. Entra a **Miembros**: la app dice que no tienes permiso. **Di:** "El tesorero maneja el dinero, no ve la lista de miembros."

### 6. Presbítero: reporte financiero (2 min)

1. Con el **presbítero**, menú → **Reporte financiero**.
2. **Muestra** el **balance** del Presbiterio (ingresos menos gastos, sin anulados) y las barras de ingresos por tipo y gastos por categoría.
3. Toca una iglesia de la lista **Por iglesia**: ve solo su detalle. Cambia el periodo a **Mes pasado**.
4. **Di:** "El pastor y el tesorero ven solo el reporte de su iglesia."

### 7. Líder de célula y ujier: asistencia en el celular (2 min)

1. Entra como **líder de célula**. Menú → **Asistencia**.
2. Con **una sola mano**, toca a cada persona que asistió. **Muestra** el conteo de abajo y toca **Guardar**.
3. Entra como **ujier**: aparece la lista de personas **sin célula**. **Di:** "El ujier marca quién faltó."
4. **Di:** "Cada líder solo marca a su célula."

### 8. Miembros y grupos (1 min)

1. Menú → **Miembros**: busca por nombre (sin importar acentos) y usa el filtro por **estado** (activo, visitante, en proceso de ganar, de consolidar, de discipular o inactivo).
2. Menú → **Grupos**: filtra por tipo (redes, células, ministerios, escuelas y áreas). Cada grupo muestra su **líder** y su **asistente**.

### Cierre

Menú → **Cerrar sesión**. **Di** qué falta (sección 4) y qué sigue.

## 3. Si hay poco tiempo

Haz solo estos cuatro pasos (6 minutos): **1** (público), **7** (asistencia), **5** (ingresos y anular) y **4** (límites al crear usuarios).

## 4. Preguntas que pueden hacer

- **¿Quién ve el dinero?** El pastor y el tesorero de su iglesia, y el presbítero en todas. El apoyo del pastor, por ahora no *(provisional, pendiente de la clienta)*.
- **¿Se puede borrar un ingreso o un gasto?** No: se **anulan con motivo** y quedan registrados.
- **¿Cada quién ve todo?** No: cada cargo ve solo su área; el pastor, su iglesia; el presbítero, todo.
- **¿Y si alguien se equivoca de cargo al crear a una persona?** Un usuario no se borra, se desactiva; y nadie puede subir a alguien a un cargo con más acceso al dinero del que él mismo tiene.
- **¿Funciona sin internet?** No, necesita conexión.
- **¿Qué falta?** Niños y adolescentes, asignar miembros a las células, eventos, comunicados y el reporte de asistencia.
- **¿Qué está pendiente de decidir con la clienta?**
  - Si el apoyo del pastor ve el dinero.
  - Quién puede anular, y si el tesorero necesita aprobación del pastor antes de gastar o anular.
  - De dónde sale el "área" de cada usuario.
  - Las opciones de estado civil de un miembro.
  - Qué ve la esposa de pastor, el diácono, el ministro y el encargado de área.
  - Cómo se cambia o restablece una contraseña.

## 5. Si algo falla durante la demo

| Pasa esto | Qué hacer |
|---|---|
| Una pantalla dice **"No se pudo conectar con el servidor"** | Revisa el internet y toca **Reintentar**. Si sigue, la API no responde: salta a otra parte de la demo y avisa a Marcos. |
| Sale **"No tienes permiso…"** donde no lo esperabas | Revisa con qué cargo entraste; puede ser la cuenta equivocada. |
| La app te manda a la pantalla de entrada | La sesión se venció (dura poco): vuelve a entrar. |
| Falta un dato de ejemplo (por ejemplo, no hay miembros) | Salta ese paso; no inventes datos delante de la clienta. |
