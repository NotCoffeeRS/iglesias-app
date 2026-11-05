import { CARGOS } from '../../api/usuarios'
import type { ModuloRutas } from '../../componentes/tipos'
import PaginaReporte from './PaginaReporte'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/reporte-asistencia', element: <PaginaReporte /> },
]
export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/reporte-asistencia',
    etiqueta: 'Reporte de asistencia',
    orden: 45,
    seccion: 'personas',
    icono: 'reporte',
    cargos: CARGOS.map((c) => c.clave).filter((c) => c !== 'tesorero'),
    descripcion: 'Asistencias y faltas por periodo e iglesia',
  },
]
