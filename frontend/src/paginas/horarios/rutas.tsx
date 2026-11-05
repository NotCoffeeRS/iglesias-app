import type { ModuloRutas } from '../../componentes/tipos'
import PaginaHorarios from './PaginaHorarios'

export const rutas: ModuloRutas['rutas'] = [{ path: '/horarios', element: <PaginaHorarios /> }]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/horarios',
    etiqueta: 'Horarios',
    orden: 15,
    seccion: 'iglesia',
    icono: 'horarios',
    descripcion: 'Cultos, oración, jóvenes y más por sede',
  },
]
