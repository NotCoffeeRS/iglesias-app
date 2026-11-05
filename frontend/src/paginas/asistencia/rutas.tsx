import type { ModuloRutas } from '../../componentes/tipos'
import { CARGOS_QUE_MARCAN_ASISTENCIA } from '../../componentes/cargos'
import PaginaAsistencia from './PaginaAsistencia'

export const rutas: ModuloRutas['rutas'] = [{ path: '/asistencia', element: <PaginaAsistencia /> }]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/asistencia',
    etiqueta: 'Asistencia',
    orden: 5,
    seccion: 'personas',
    icono: 'asistencia',
    cargos: CARGOS_QUE_MARCAN_ASISTENCIA,
    descripcion: 'Marca quién asistió al culto o quién faltó',
  },
]
