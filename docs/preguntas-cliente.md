# Preguntas para la clienta (entrevista de requisitos)

Quien responde: la hermana de Marcos, que asiste a una iglesia cristiana y será la usuaria de referencia.
Cómo usarlo: Marcos hace las preguntas con calma (platicando, no como examen), anota la respuesta tal cual y
después el equipo la pasa a `docs/DECISIONES.md`. **Lo que no se responda queda como suposición** y se avisa en el Sprint.
Si la respuesta es "no sé", anótalo así; es un dato útil.

No se piden ni se anotan datos reales de personas: para las pruebas usamos nombres inventados.

## 0. Las 5 que no pueden faltar (si solo hay 10 minutos)

1. Si el 1 de noviembre la app solo pudiera hacer **3 cosas**, ¿cuáles serían?
2. ¿Cuántas iglesias hay realmente y quién se encarga de cada una? ¿Hay una sede principal?
3. ¿Quién va a usar la app (pastor, secretaria, tesorero, líderes, miembros) y quién **no** debe ver el dinero?
4. ¿Hoy cómo llevan todo esto (cuaderno, Excel, WhatsApp)? ¿Qué es lo que más trabajo les cuesta?
5. ¿La usarán más desde el celular o desde una computadora?

## 1. Iglesias, horarios y ubicaciones

- ¿Qué datos de cada iglesia quieren ver (nombre, dirección, teléfono, pastor, foto, redes sociales)?
- ¿Qué tipos de servicio hay (domingo, entre semana, oración, jóvenes, niños, células)? ¿Los horarios cambian por temporada o fecha especial?
- ¿Les basta un enlace a Google Maps o quieren ver un mapa dentro de la app?
- ¿Los visitantes (sin cuenta) deberían poder consultar horarios y ubicaciones?

## 2. Usuarios y roles

- ¿Qué cargos existen (pastor, administrador de sede, tesorero, secretaria, líder de ministerio, diácono)? ¿Qué debe poder hacer cada uno?
- ¿Cada sede maneja solo su información o hay alguien que ve todas?
- ¿Los miembros comunes tendrán cuenta para entrar, o solo la use el personal?
- ¿Quién da de alta a los usuarios y quién recupera una contraseña olvidada?

## 3. Miembros

- ¿Qué datos se guardan de un miembro (nombre, teléfono, correo, fecha de nacimiento, dirección, estado civil, fecha de bautizo, familia)?
- ¿Qué estados manejan (miembro activo, visitante, inactivo, en proceso de membresía)?
- ¿Un miembro puede cambiar de sede? ¿Se lleva historial?
- ¿Se registra a los niños? ¿Con qué datos?
- ¿Hay algo que **no** deba guardarse por privacidad?

## 4. Asistencia

- ¿Se pasa lista nombre por nombre o solo se cuenta cuánta gente hubo?
- ¿A qué se le toma asistencia (cada servicio, eventos, ministerios, escuela dominical)?
- ¿Quién la registra y desde dónde (celular a la entrada, computadora después)?
- ¿Cómo cuentan a las visitas y a los niños?

## 5. Eventos

- ¿Qué tipos de evento hay (retiros, bautizos, bodas, conferencias, campañas, convivios)?
- ¿Son por sede o para toda la red? ¿Tienen costo, cupo o inscripción?
- ¿Quieren recordatorios? ¿Por dónde (WhatsApp, correo, solo dentro de la app)?

## 6. Ministerios

- ¿Qué ministerios existen (alabanza, jóvenes, niños, damas, caballeros, diaconado, intercesión)?
- ¿Son por sede o de toda la red? ¿Tienen líder y colíder?
- ¿Un miembro puede estar en varios ministerios? ¿Los ministerios tienen reuniones propias?

## 7. Donaciones y aportaciones (dato sensible)

- ¿Qué tipos hay (diezmo, ofrenda, pro-templo, misiones, ayuda social, ofrendas especiales)?
- ¿Se registra **quién** dio o puede ser anónimo? ¿Quién debe poder ver quién dio?
- ¿Cómo reciben el dinero (efectivo, transferencia, tarjeta)? ¿Todo en pesos?
- ¿Quién lo cuenta y lo registra, y cada cuánto (cada servicio, cada semana)?
- ¿Dan recibo o constancia a quien lo pide?
- ¿Una parte se envía a una sede central o a un fondo común?
- Si se captura mal un monto, ¿cómo lo corrigen hoy y quién autoriza?

## 8. Gastos y costos

- ¿Qué categorías de gasto hay (luz, agua, renta, mantenimiento, apoyo pastoral, material, eventos, ayuda social, transporte)?
- ¿Alguien tiene que autorizar un gasto antes de hacerlo? ¿A partir de qué monto?
- ¿Guardan comprobantes o facturas? ¿Quieren adjuntar una foto?
- ¿Manejan un presupuesto mensual por sede? ¿Separan gastos fijos de costos de eventos?

## 9. Comunicados y anuncios

- ¿A quién van dirigidos (todos, una sede, un ministerio)? ¿Quién los publica?
- ¿Cuánto tiempo deben seguir visibles?
- ¿Quieren que además lleguen por WhatsApp o correo, o basta verlos en la app?

## 10. Reportes

- ¿Qué reportes necesitan de verdad (asistencia, ingresos, gastos, balance, miembros nuevos)? ¿Cada cuánto (semanal, mensual, anual)?
- ¿Quién los ve y a quién se los presentan (pastor, congregación, junta)?
- ¿Necesitan descargarlos en Excel o PDF?

## 11. Imagen y lenguaje

- ¿Usan palabras propias que la app debe respetar (hermano/a, célula, grupo de casa, discipulado, diezmo)?
- ¿Hay logo, colores o un nombre para la app?
- ¿Hay internet estable en las sedes? ¿Qué celulares usan más?

## Respuestas

### 29 oct 2026 — primera tanda (secciones 0, 1 y 2)

- Presbiterio de la 3ra IAFCJ: 3ra de Mérida (pastor Jorge Lozano; 2 sedes: Madero y Kanasín), 4ta (Isaac Euan), 6ta (Manuel Ortega), Huhí (Jeremías Camaal). Sin sede principal; rinden cuentas al pastor de la 3ra.
- Usuarios: pastores, secretarios/as, tesoreros, líderes. Dinero: solo pastor y tesorero de su iglesia; el pastor Lozano, de todas.
- Hoy lo llevan en Excel y libretas. Uso en celular y computadora, más en celular.
- Datos de iglesia: nombre, foto de fachada, dirección, pastor, teléfono del pastor y de la iglesia (opcionales), redes sociales propias y relacionadas.
- Servicios: cultos de domingo (horario varía), entre semana (la 6ta tiene miércoles), oración, jóvenes, DNA, ministerios, escuelas (IBID), células. Los horarios casi no cambian.
- Ubicación: enlace de Google Maps (colección de la clienta). Horarios y ubicaciones públicos; el resto solo liderazgo.
- Cargos: pastor y esposa, tesoreros, líderes de red (varones, damas, jóvenes), líderes y asistentes de célula, líderes de ministerio (con asistente o segundo), diáconos, ministros, encargados de área (p. ej. la tiendita). Cada cargo ve solo su área; el pastor ve toda su iglesia; el presbítero, todo. Cada pastor tiene una persona de apoyo con la app.

**Sin responder aún:** miembros, asistencia, eventos, ministerios (detalle), donaciones, gastos, comunicados, reportes, imagen y lenguaje, y si el apoyo del pastor ve el dinero.

### 30 oct 2026 — segunda tanda (miembros, asistencia, donaciones, gastos)

- Miembros: sí se registran, con nombre y desde cuándo forman parte de la congregación. Datos: todos los propuestos menos familia. Estados: miembro activo, miembro inactivo, visitante, en proceso de ganar, en proceso de discipular, en proceso de consolidar.
- Niños y adolescentes: nombre, nacimiento, dirección, niño o niña (4 a 11 años) o adolescente (12 a 17) y tutores.
- Privacidad: no se le ocurre nada por ahora.
- Asistencia: cada líder anota quién de su célula asistió al culto (domingo, miércoles u otro día). Para quienes no tienen célula, el ujier (en la puerta) ve quién faltó; los ujieres cambian según el rol asignado.
- Ingresos: diezmos, ofrendas, EVAMI (evangelismo misionero), talento (venta de comida) y otras donaciones con descripción. Solo se manejan cantidades (ej.: lo recaudado el culto del domingo 1 de septiembre, y una petición para la operación de una hermana).
- Gastos: luz, agua, renta, mantenimiento, material de construcción, materiales (limpieza, reposición de algo que se rompa), apoyo a miembros, etc. Sí hay autorización: tesorería en sujeción al pastor local.

### 5 nov 2026 — tercera tanda

- **Apoyo del pastor y dinero:** quiere que el pastor tenga un botón para dar acceso al dinero a cualquier cargo; por defecto solo lo ven el pastor y el tesorero.
- **Horarios:** 3ra Madero, domingos 5:30 pm; 3ra Kanasín, domingos 11:30 am; 6ta, 6 pm; 4ta y Huhí, no sabe.
- **Dos cargos:** sí, una persona puede tener dos.
- **Asistencia:** todos los grupos la toman; la registra el líder o maestro, hoy en listas físicas. Registrar visitas y niños estaría bien empezar.
- **Células:** tienen sus propios miembros y reportes (asistencia y ofrenda); reportan al pastor local. Mandará la foto del reporte. Una célula por miembro como ideal; podría asistir a varias.
- **Eventos:** por iglesia local, salvo congresos (distritales). Tipos del proceso de discipulado más presentación de niños, bodas, XV años, graduación IBID y congresos. Cuota según cada iglesia; congresos con costo. Recordatorios dentro de la app.
- **Ingresos:** efectivo, lo cuenta el tesorero; rendición y recibo según el pastor local. El pastor local corrige montos sin autorización.
- **Gastos:** guardar comprobantes con foto adjunta. Presupuesto según cada iglesia. Áreas como la tiendita llevan sus cuentas aparte, con posible inversión desde las ofrendas o el pastor.
- **Comunicados:** por iglesia local, los publica multimedia o el pastor o alguien de confianza; visibles para siempre o al menos un año; también por WhatsApp.
- **Imagen:** logo de la IAFCJ. No hay internet estable en todas las iglesias.
- No entendió la pregunta de las palabras propias de la app (35); no pidió dato de envío a la 3ra o fondo (21), que prefirió no preguntar.

