# Frontend de Iglesias App

React 19 + Vite + TypeScript + Tailwind CSS 4, con React Router. Pensado para celular primero.

## Cómo correrlo

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

| Comando          | Qué hace                                          |
| ---------------- | ------------------------------------------------- |
| `npm run dev`    | Servidor de desarrollo                            |
| `npm run lint`   | ESLint                                            |
| `npm run build`  | Revisión de tipos (`tsc`) y compilación a `dist/` |
| `npm run format` | Da formato con Prettier                           |

## Variables de entorno

| Variable       | Para qué                     | Valor por defecto       |
| -------------- | ---------------------------- | ----------------------- |
| `VITE_API_URL` | URL base de la API (FastAPI) | `http://localhost:8000` |

Para cambiarla en local crea `frontend/.env.local` (no se sube al repositorio):

```
VITE_API_URL=http://localhost:8000
```

## Cómo agregar pantallas (sin tocar el enrutador)

Cada módulo vive en su carpeta `src/paginas/<modulo>/` y tiene un archivo `rutas.tsx`.
`App.tsx` encuentra esos archivos solo (con `import.meta.glob`), así que **ninguna tarea edita `App.tsx`**.

```tsx
// src/paginas/miembros/rutas.tsx
import type { ModuloRutas } from '../../componentes/tipos'
import ListaMiembros from './ListaMiembros'

export const rutas: ModuloRutas['rutas'] = [{ path: '/miembros', element: <ListaMiembros /> }]

// Opcional: enlace en el menú (menor orden = más arriba).
// Con `descripcion`, además aparece como acceso en el mosaico de Inicio.
export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/miembros',
    etiqueta: 'Miembros',
    orden: 30,
    descripcion: 'Registro y estado de cada miembro',
  },
]

// Opcional: pantallas sin encabezado ni menú (p. ej. inicio de sesión)
// export const rutasSinLayout: ModuloRutas['rutasSinLayout'] = [{ path: '/login', element: <Login /> }]
```

- `rutas` se muestran dentro del layout (encabezado y menú).
- Si ningún módulo define `/`, se muestra la bienvenida de `componentes/Inicio.tsx`.
- Cualquier ruta desconocida muestra `componentes/NoEncontrada.tsx`.
- Un módulo puede exportar `envoltorio`, un componente que rodea al layout y a **todas** sus rutas
  (lo usa el módulo de sesión para mandar al login a quien no tenga sesión). Las páginas públicas,
  como horarios y ubicaciones, van en `rutasSinLayout` para no pasar por él.

## Llamar a la API

Usa siempre `src/api/cliente.ts`; agrega el token de sesión (`Authorization: Bearer …`) y la URL base:

```ts
import { api, ErrorApi, guardarToken } from '../../api/cliente'

const miembros = await api.get<Miembro[]>('/miembros')
await api.post('/miembros', { nombre: 'Ana Ejemplo' })
```

Si la respuesta no es exitosa lanza `ErrorApi` con `estado` (código HTTP, `0` sin conexión) y un mensaje
en español tomado del `detail` de FastAPI. `guardarToken` / `borrarToken` manejan la sesión.
Si la API responde 401 a una petición que llevaba token (sesión vencida), el cliente borra el token
y emite el evento `EVENTO_SESION_EXPIRADA` en `window`.

## Diseño

- **Colores por función**, nunca fijos (`bg-white`, `text-slate-700`…). Así la app cambia sola a modo oscuro:

| Clase                               | Uso                                                      |
| ----------------------------------- | -------------------------------------------------------- |
| `bg-fondo`                          | Fondo de la página                                       |
| `bg-superficie` / `bg-superficie-2` | Tarjetas y paneles / zonas hundidas o al pasar el cursor |
| `border-borde`                      | Bordes y divisiones                                      |
| `text-texto` / `text-texto-suave`   | Texto principal / secundario                             |
| `bg-primario text-sobre-primario`   | Botón principal (`hover:bg-primario-hover`)              |
| `bg-acento text-acento-texto`       | Elemento seleccionado o destacado                        |
| `text-enlace`                       | Enlaces                                                  |
| `text-peligro bg-peligro-fondo`     | Errores                                                  |

- **Tipografía:** `font-titulo` (Bricolage Grotesque) en títulos; el texto usa Atkinson Hyperlegible Next.
  Los `h1`, `h2` y `h3` ya usan `font-titulo`.
- Esquinas: `rounded-xl` en botones y campos, `rounded-2xl`/`rounded-3xl` en tarjetas.
- Sin etiquetas en MAYÚSCULAS ni animaciones decorativas; el movimiento solo responde a acciones.

## Estructura

```
src/
  main.tsx            arranque
  App.tsx             enrutador (descubre src/paginas/*/rutas.tsx)
  index.css           Tailwind, tipografías y colores por función (modo claro y oscuro)
  api/cliente.ts      cliente HTTP
  componentes/        Layout, Inicio, NoEncontrada y tipos compartidos
  paginas/<modulo>/   una carpeta por módulo, con su rutas.tsx
```
