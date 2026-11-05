import type { ModuloRutas } from '../../componentes/tipos'
import FormularioEvento from './FormularioEvento'
import PaginaEventos from './PaginaEventos'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/eventos', element: <PaginaEventos /> },
  { path: '/eventos/nuevo', element: <FormularioEvento /> },
  { path: '/eventos/:id/editar', element: <FormularioEvento /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/eventos',
    etiqueta: 'Eventos',
    orden: 70,
    seccion: 'iglesia',
    icono: 'eventos',
    descripcion: 'Retiros, bautizos y más',
  },
]
