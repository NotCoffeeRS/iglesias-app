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

// Opcional: enlace en el menú (menor orden = más arriba)
export const menu: ModuloRutas['menu'] = [{ ruta: '/miembros', etiqueta: 'Miembros', orden: 30 }]

// Opcional: pantallas sin encabezado ni menú (p. ej. inicio de sesión)
// export const rutasSinLayout: ModuloRutas['rutasSinLayout'] = [{ path: '/login', element: <Login /> }]
```

- `rutas` se muestran dentro del layout (encabezado y menú).
- Si ningún módulo define `/`, se muestra la bienvenida de `componentes/Inicio.tsx`.
- Cualquier ruta desconocida muestra `componentes/NoEncontrada.tsx`.

## Llamar a la API

Usa siempre `src/api/cliente.ts`; agrega el token de sesión (`Authorization: Bearer …`) y la URL base:

```ts
import { api, ErrorApi, guardarToken } from '../../api/cliente'

const miembros = await api.get<Miembro[]>('/miembros')
await api.post('/miembros', { nombre: 'Ana Ejemplo' })
```

Si la respuesta no es exitosa lanza `ErrorApi` con `estado` (código HTTP, `0` sin conexión) y un mensaje
en español tomado del `detail` de FastAPI. `guardarToken` / `borrarToken` manejan la sesión.

## Estructura

```
src/
  main.tsx            arranque
  App.tsx             enrutador (descubre src/paginas/*/rutas.tsx)
  index.css           Tailwind y colores (bg-primario, text-acento, …)
  api/cliente.ts      cliente HTTP
  componentes/        Layout, Inicio, NoEncontrada y tipos compartidos
  paginas/<modulo>/   una carpeta por módulo, con su rutas.tsx
```
