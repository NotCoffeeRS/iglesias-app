import type { ModuloRutas } from '../../componentes/tipos'
import PaginaAsistencia from './PaginaAsistencia'

export const rutas: ModuloRutas['rutas'] = [{ path: '/asistencia', element: <PaginaAsistencia /> }]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/asistencia',
    etiqueta: 'Asistencia',
    orden: 5,
    descripcion: 'Marca quién asistió al culto o quién faltó',
  },
]
