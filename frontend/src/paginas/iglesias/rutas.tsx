import type { ModuloRutas } from '../../componentes/tipos'
import FichaIglesia from './FichaIglesia'
import FormularioIglesia from './FormularioIglesia'
import ListaIglesias from './ListaIglesias'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/iglesias', element: <ListaIglesias /> },
  { path: '/iglesias/:id', element: <FichaIglesia /> },
  { path: '/iglesias/:id/editar', element: <FormularioIglesia /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/iglesias',
    etiqueta: 'Iglesias',
    orden: 10,
    descripcion: 'Ficha, sedes y redes de cada iglesia',
  },
]
