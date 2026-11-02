import { createBrowserRouter, RouterProvider, type RouteObject } from 'react-router-dom'
import Inicio from './componentes/Inicio'
import Layout from './componentes/Layout'
import NoEncontrada from './componentes/NoEncontrada'
import type { EntradaMenu, ModuloRutas } from './componentes/tipos'

// Descubre solo cada src/paginas/<modulo>/rutas.tsx. Para agregar pantallas basta con crear
// la carpeta del módulo y su rutas.tsx; este archivo no se edita.
const modulos = Object.values(
  import.meta.glob<ModuloRutas>('./paginas/*/rutas.tsx', { eager: true }),
)

const rutas: RouteObject[] = modulos.flatMap((m) => m.rutas ?? [])
const rutasSinLayout: RouteObject[] = modulos.flatMap((m) => m.rutasSinLayout ?? [])
const menu: EntradaMenu[] = modulos
  .flatMap((m) => m.menu ?? [])
  .sort(
    (a, b) =>
      (a.orden ?? Infinity) - (b.orden ?? Infinity) || a.etiqueta.localeCompare(b.etiqueta, 'es'),
  )

// Si ningún módulo define la ruta "/", se muestra la bienvenida por defecto.
const hayInicio = rutas.some((r) => r.index || r.path === '/' || r.path === '')

const enrutador = createBrowserRouter([
  {
    path: '/',
    element: <Layout menu={menu} />,
    children: [
      ...(hayInicio ? [] : [{ index: true, element: <Inicio /> }]),
      ...rutas,
      { path: '*', element: <NoEncontrada /> },
    ],
  },
  ...rutasSinLayout,
])

export default function App() {
  return <RouterProvider router={enrutador} />
}
