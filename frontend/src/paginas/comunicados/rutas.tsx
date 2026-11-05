import type { ModuloRutas } from '../../componentes/tipos'
import FormularioComunicado from './FormularioComunicado'
import PaginaComunicados from './PaginaComunicados'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/comunicados', element: <PaginaComunicados /> },
  { path: '/comunicados/nuevo', element: <FormularioComunicado /> },
  { path: '/comunicados/:id/editar', element: <FormularioComunicado /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/comunicados',
    etiqueta: 'Comunicados',
    orden: 75,
    descripcion: 'Avisos y anuncios',
  },
]
