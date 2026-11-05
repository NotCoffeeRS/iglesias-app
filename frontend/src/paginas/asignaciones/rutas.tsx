import { CARGOS_CON_MIEMBROS_Y_GRUPOS } from '../../componentes/cargos'
import type { ModuloRutas } from '../../componentes/tipos'
import PaginaAsignaciones from './PaginaAsignaciones'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/asignaciones', element: <PaginaAsignaciones /> },
]
export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/asignaciones',
    etiqueta: 'Asignaciones',
    orden: 35,
    seccion: 'personas',
    descripcion: 'Integrantes de grupos y células',
    cargos: CARGOS_CON_MIEMBROS_Y_GRUPOS,
  },
]
