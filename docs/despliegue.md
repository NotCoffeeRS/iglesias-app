# Despliegue de la demo — Iglesias App

Guía para publicar la demo y poder **repetirla**. Se usan tres servicios gratuitos: **Neon** (base de datos PostgreSQL), **Render** (API) y **Vercel** (la web).
Todo lo que sigue lo hace **Marcos con sus propias cuentas**. En el repositorio **no se guarda ninguna contraseña, cadena de conexión ni clave**: se escriben solo en el panel de cada servicio.

> **Estado al 4 nov 2026.** El backend todavía no tiene las APIs de iglesias, horarios, miembros, grupos, asistencia, ingresos y gastos (Issues #12, #14, #17, #20, #23, #25, #27), ni CORS, ni los datos de ejemplo (#5). Desplegar hoy mostraría el inicio de sesión y las pantallas, pero la mayoría diría "No se pudo conectar". Esta guía está lista para cuando esas piezas estén en `main`.

## Orden recomendado

1. Neon (base de datos) → 2. Render (API) → 3. Vercel (web) → 4. Conectar los tres → 5. Datos de ejemplo → 6. Revisar.

## 1. Base de datos en Neon

1. Crea un proyecto en https://neon.tech (plan gratuito). Elige la **versión 17 de PostgreSQL** (las pruebas del equipo se corrieron con la 16 y la 17; confirma cuál usa tu proyecto y anótalo en `docs/DECISIONES.md`).
2. Región cercana a la de Render.
3. Copia la **cadena de conexión** (Connection string) y cámbiale el inicio:
   - Neon la entrega como `postgresql://usuario:contraseña@host/base?sslmode=require`.
   - La API la necesita como `postgresql+psycopg://usuario:contraseña@host/base?sslmode=require`.
4. **No la pegues en el chat, en un Issue ni en un archivo del repositorio.** Solo en el panel de Render (paso 2).

## 2. API en Render

1. En https://render.com crea un **Web Service** desde el repositorio `NotCoffeeRS/iglesias-app` (rama `main`).
2. Configuración:

   | Campo | Valor |
   |---|---|
   | Root Directory | `backend` |
   | Runtime | Python 3 (3.12) |
   | Build Command | `pip install .` |
   | Start Command | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Health Check Path | `/salud` |

   El `alembic upgrade head` del arranque aplica la migración (tablas) cada vez que se despliega. Es seguro repetirlo: no hace nada si ya está al día.

3. Variables de entorno (se escriben en el panel de Render, **nunca** en el repositorio):

   | Variable | Qué poner |
   |---|---|
   | `DATABASE_URL` | La cadena de Neon del paso 1, con `postgresql+psycopg://` |
   | `SECRET_KEY` | Un secreto aleatorio de 32 bytes o más. Para generarlo: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Distinto al de tu computadora |
   | `CORS_ORIGINS` | La dirección de la web en Vercel (paso 3). **Pendiente:** esta variable la usará el CORS que está por hacer Ángeles; ver "Pendientes" |

4. Cuando termine, abre `https://<tu-servicio>.onrender.com/salud`: debe responder que está bien.
5. **Aviso del plan gratuito:** Render duerme el servicio tras unos minutos sin uso y la primera petición tarda ~30–60 segundos. **Antes de presentar, abre la dirección de la API una vez** para despertarla.

## 3. Web en Vercel

1. En https://vercel.com importa el mismo repositorio.
2. Configuración:

   | Campo | Valor |
   |---|---|
   | Framework Preset | Vite |
   | Root Directory | `frontend` |
   | Build Command | `npm run build` |
   | Output Directory | `dist` |

3. Variable de entorno: `VITE_API_URL` = la dirección de la API en Render, **sin diagonal al final** (por ejemplo `https://iglesias-api.onrender.com`).
4. `frontend/vercel.json` ya incluye la regla que manda cualquier ruta a `index.html`; sin ella, recargar `/ubicaciones` o `/gastos` daría 404.
5. **Importante:** `VITE_API_URL` se "congela" al construir la web. Si cambias la dirección de la API, hay que volver a desplegar en Vercel.

## 4. Conectar los tres

- Pon en Render `CORS_ORIGINS` con la dirección exacta de Vercel (con `https://` y sin diagonal final). Vuelve a desplegar la API.
- Prueba desde el celular: abre la web, entra al inicio de sesión y revisa que no diga "No se pudo conectar".

## 5. Datos de ejemplo (Issue #5, de Jessica)

La demo necesita las 4 iglesias (la 3ra de Mérida con 2 sedes), horarios, miembros y una cuenta por cargo (presbítero, pastor, apoyo, tesorero, líder de célula y ujier). Todos los nombres de personas, teléfonos y montos son **inventados**.

- Se cargan con el script de Jessica (`backend/scripts/cargar_datos_ejemplo.py`) apuntando a la base de Neon. Por seguridad hay que **correrlo desde tu computadora** con `DATABASE_URL` puesta solo en esa terminal, no desde el repositorio.
- **Las contraseñas de las cuentas de ejemplo no se guardan en el repositorio:** Jessica o Marcos las pasan por otro medio.
- El script debe poder repetirse sin duplicar datos.

## 6. Lista de revisión antes de presentar

- [ ] `https://<api>/salud` responde (despierta la API primero).
- [ ] La web carga en el celular y `/ubicaciones` se ve sin iniciar sesión.
- [ ] Entras con la cuenta de presbítero y ves iglesias y reportes.
- [ ] La cuenta de apoyo **no** ve el dinero; la del tesorero **no** ve la lista de miembros.
- [ ] Recargar una pantalla interna (por ejemplo `/gastos`) no da 404.
- [ ] Ningún archivo del repositorio contiene claves ni cadenas de conexión.

## Pendientes antes de poder desplegar de verdad

| Qué | De quién |
|---|---|
| CORS en la API (lee `CORS_ORIGINS`) | Ángeles |
| APIs de iglesias, horarios, miembros, grupos, asistencia, ingresos y gastos | Ángeles y Vanessa |
| Datos de ejemplo (#5) | Jessica |
| Confirmar la versión de PostgreSQL de Neon | Marcos |

## Si algo falla

| Pasa esto | Qué hacer |
|---|---|
| La web dice "No se pudo conectar con el servidor" | Revisa `VITE_API_URL` en Vercel, vuelve a desplegar, y despierta la API de Render |
| El navegador bloquea las peticiones (error CORS en la consola) | Revisa que `CORS_ORIGINS` sea exactamente la dirección de Vercel |
| La API no arranca en Render | Revisa los registros del servicio: suele ser `DATABASE_URL` mal escrita o `SECRET_KEY` de menos de 32 bytes |
| Recargar una pantalla da 404 | Falta `frontend/vercel.json` en esa versión de la web |
