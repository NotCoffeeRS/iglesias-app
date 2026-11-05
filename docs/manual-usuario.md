# Manual de usuario — Iglesias App

Aplicación web del Presbiterio de la 3ra IAFCJ. Se usa sobre todo desde el celular, y también desde la computadora.
Este manual es corto: primero lo básico, después lo que hace cada cargo y, al final, cómo se hace cada tarea.

> **Estado de este documento (3 nov 2026).** Describe las pantallas ya construidas. Todavía **no** están: niños y adolescentes,
> asignar miembros a las células, eventos, comunicados y el reporte de asistencia; por eso no aparecen aquí.
> Lo marcado como *(provisional)* es una regla que la clienta aún no confirma (ver `docs/DECISIONES.md`).
> Los ejemplos usan nombres inventados: en este manual no hay datos reales de personas ni de dinero.

## 1. Lo básico

- **Entrar.** Abre la dirección de la app, escribe tu **usuario** y tu **contraseña** y toca **Entrar**. Tu pastor o su apoyo te da la cuenta.
- **Menú.** En el celular, toca el icono de las tres rayas (arriba a la izquierda). En la computadora, el menú está a la izquierda.
  Solo debes usar lo que te toca: si entras a algo que tu cargo no puede ver, la app te lo dice y no muestra nada.
- **Cerrar sesión.** Al final del menú. Hazlo siempre si usas un celular que no es tuyo.
- **Si la sesión se vence**, la app te regresa a la pantalla de entrada; vuelve a entrar.
- **Sin cuenta** puedes ver los horarios y cómo llegar a cada iglesia en la dirección `/ubicaciones`. Es lo único público.
- **Modo oscuro.** La app se pone oscura sola si tu celular está en modo oscuro.
- **Los permisos los decide el servidor**, no los botones: aunque conozcas una dirección, si tu cargo no puede entrar, no entra.

## 2. Palabras de la iglesia que usa la app

| Palabra | Cómo la usa la app |
|---|---|
| **Presbiterio** | El conjunto de las 4 iglesias. La 3ra de Mérida tiene 2 sedes (Madero y Kanasín); las demás, una. |
| **Presbítero** | Quien ve todo el Presbiterio. Las 4 iglesias le rinden cuentas. |
| **Apoyo del pastor** | La persona que usa la app por el pastor. La clienta lo llama a veces "secretario o secretaria" *(provisional)*. |
| **Red** | Grupo de la iglesia por tipo de persona: de varones, de damas o de jóvenes. Tiene líder. |
| **Célula** | Grupo con su líder y su asistente. Del líder de célula sale la asistencia. |
| **Ministerio** | Grupo de servicio de la iglesia, con líder y asistente o "segundo". |
| **Escuela (IBID)** | IBID es el *Instituto Bíblico Distrital*. En la app, las escuelas son un tipo de grupo y un tipo de horario. |
| **DNA** | *Discipulando Niños y Adolescentes*. Es uno de los tipos de servicio con horario, junto con culto de domingo, culto entre semana, oración, jóvenes, escuela, célula y ministerio. |
| **Área** | Un servicio a cargo de alguien, como la tiendita. Es un tipo de grupo. |
| **Ujier** | Quien está en la puerta. Es un cargo que rota. |
| **Diezmos y ofrendas** | Dos de los tipos de ingreso. |
| **EVAMI** | Evangelismo misionero. Es un tipo de ingreso. |
| **Talento** | Lo recaudado con la venta de comida. Es un tipo de ingreso. |
| **Otras donaciones** | Ingresos que no son de los tipos anteriores. Siempre llevan una descripción. |
| **Anular** | Marcar un ingreso o un gasto como invalidado, con su motivo. **Nunca se borra** y deja de contar en los totales. |

## 3. Qué hace cada cargo

Regla general: **cada cargo ve solo lo de su área; el pastor ve toda su iglesia; el presbítero ve todo.**
El dinero (ingresos, gastos y reporte) lo ven **solo** el pastor y el tesorero de su iglesia, y el presbítero en todas.

### Presbítero

- Ve **todo el Presbiterio**, incluido el dinero de las 4 iglesias y el **consolidado** del reporte financiero.
- Edita los datos de **cualquier** iglesia y sus horarios.
- Es el **único que crea pastores**. No crea a otro presbítero desde la app.
- Es el único que crea eventos y comunicados para todo el Presbiterio.

### Pastor

- Ve **toda su iglesia**: miembros, grupos, asistencia, dinero y reporte financiero.
- Edita la ficha y los horarios de **su** iglesia, no los de otra.
- Crea usuarios de su iglesia con cualquier cargo **menos pastor y presbítero**; puede crear al **tesorero**.
- Crea eventos y comunicados solo para su iglesia.

### Apoyo del pastor

- Usa la app **por el pastor**, dentro de su iglesia. Edita la ficha de su iglesia (no la de otra).
- Crea y edita usuarios **solo con cargos sin acceso al dinero**: no puede crear tesorero ni pastor, ni subir a alguien a esos cargos.
- Crea eventos y comunicados solo para su iglesia.
- **No ve el dinero** *(provisional, pendiente de la clienta)*.
- No cambia su propio cargo.

### Tesorero

- Registra **ingresos** por culto y tipo (diezmos, ofrendas, EVAMI, talento y otras) y **gastos**.
- **Anula** ingresos y gastos de su iglesia con motivo, sin pedir aprobación antes al pastor *(provisional)*.
- Ve el **reporte financiero de su iglesia**.
- **No ve la lista de miembros.**
- Los gastos se llevan "en sujeción al pastor local"; cómo se autoriza cada gasto sigue por confirmar con la clienta.

### Líder de célula

- Marca en **Asistencia** quién de su célula **asistió** al culto (domingo, entre semana u otro día).
- Solo ve y administra **su** célula.

### Líder de red y líder de ministerio

- Ven y administran **su** red o **su** ministerio, con su asistente o segundo.
- No ven el dinero.

### Asistente

- Apoya al líder de su célula o ministerio. Ve lo de su área; no ve el dinero.

### Ujier

- Es un cargo **rotativo**: cambia según el rol asignado.
- Marca en **Asistencia** quién **faltó**, solo de las personas **sin célula** de su iglesia.

### Esposa de pastor, diácono, ministro y encargado de área

- Ven lo de **su área** y no ven el dinero *(provisional, pendiente de la clienta)*. Un encargado de área cuida un servicio concreto, como la tiendita.
- Hoy no hay pantallas propias para estos cargos; si la clienta pide algo más, se agrega después.

## 4. Cómo se hace cada tarea

### Ver horarios y cómo llegar (sin cuenta)

1. Abre `/ubicaciones`.
2. Toca el nombre de una iglesia para ir a ella.
3. Toca **Cómo llegar** para abrir Google Maps. Toca el teléfono de la iglesia para llamar.

### Marcar la asistencia (líder de célula o ujier)

1. Menú → **Asistencia**.
2. Revisa la fecha y el culto; la app propone domingo o entre semana según el día.
3. Toca a cada persona: el líder toca a quien **asistió**; el ujier, a quien **faltó**. Cada fila es grande para usarla con una mano.
4. Toca **Guardar**. Si ya estaba guardada, puedes corregirla.
5. Si cambias de fecha o de lista con marcas sin guardar, la app te pregunta antes de descartarlas.

### Registrar los ingresos de un culto (tesorero)

1. Menú → **Ingresos** → **Registrar ingresos**.
2. Elige la **fecha** y, si quieres, el **culto**.
3. Escribe solo los tipos que hubo: diezmos, ofrendas, EVAMI, talento y otras. En "otras" escribe de qué fueron.
4. Revisa el **total** de abajo y toca **Registrar**.
5. Aquí **no se anota quién dio**, solo la cantidad.

### Registrar un gasto (tesorero)

1. Menú → **Gastos** → **Registrar gasto**.
2. Elige la **fecha** y la **categoría**: luz, agua, renta, mantenimiento, material de construcción, materiales y reposiciones, apoyo a miembros u otros.
3. Escribe el **monto** y, si quieres, una nota. Toca **Registrar**.

### Anular un ingreso o un gasto

1. En **Ingresos** o **Gastos**, busca la fila y toca **Anular**.
2. Escribe el **motivo** (es obligatorio) y toca **Anular ingreso** o **Anular gasto**.
3. La fila queda tachada y con su motivo, y ya no suma en los totales. Desde la app no se puede deshacer ni borrar.

### Ver el reporte financiero (presbítero, pastor y tesorero)

1. Menú → **Reporte financiero**.
2. Elige el periodo: este mes, mes pasado, este año o tus propias fechas.
3. El número grande es el **balance**: ingresos menos gastos. Los anulados no cuentan.
4. El presbítero ve el **consolidado** y una fila por iglesia; toca una fila para ver su detalle.

### Crear un usuario (presbítero, pastor y apoyo)

1. Menú → **Usuarios** → **Crear usuario**.
2. Escribe el nombre completo, el **nombre de usuario** y una **contraseña** para empezar. Entrégasela a la persona.
3. Elige el **cargo**. La lista solo muestra los cargos que tú puedes dar.
4. Toca **Crear usuario**. Un usuario **no se borra**: si ya no debe entrar, ábrelo y quita **Cuenta activa**.

### Registrar un miembro

1. Menú → **Miembros** → **Registrar miembro**.
2. Escribe el nombre y los datos que tengas. Elige el **estado**: activo, inactivo, visitante, en proceso de ganar, de discipular o de consolidar.
3. En **Miembros** puedes **buscar por nombre** y **filtrar por estado**.

### Crear un grupo (red, célula, ministerio, escuela o área)

1. Menú → **Grupos** → **Crear grupo**.
2. Elige el **tipo**, escribe el nombre y elige la iglesia.
3. Elige al **líder** y, si quieres, al **asistente o segundo** entre los miembros de esa iglesia.

### Cambiar los horarios de una sede

1. Menú → **Horarios**. Si cuidas varias sedes, elige primero la sede.
2. **Agregar horario**: elige el tipo de servicio (culto de domingo, entre semana, oración, jóvenes, DNA, escuela, célula o ministerio), el día y la hora.
3. Para cambiar uno, toca **Editar**; para quitarlo, **Quitar** y confirma. Una sede puede tener varios horarios del mismo tipo.
4. Lo que guardes aparece en la página pública `/ubicaciones`.

### Cambiar la ficha de una iglesia

1. Menú → **Iglesias** → toca la iglesia → **Editar ficha**.
2. Puedes cambiar el nombre, la foto de la fachada (con un enlace), el pastor, los teléfonos, las redes sociales y las sedes con su enlace de Google Maps.
3. Los teléfonos son opcionales. **El teléfono del pastor no se publica.**

## 5. Cuidar los datos

- **Nunca compartas tu contraseña.** Cada persona usa su propia cuenta.
- No se guardan datos de la familia de los miembros.
- En los ingresos no se anota quién dio.
- Si algo se registró mal, **anúlalo con su motivo**; no hay forma de borrarlo.
- Si ves un error de conexión, revisa tu internet y toca **Reintentar**.
