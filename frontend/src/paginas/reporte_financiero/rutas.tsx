import type { ModuloRutas } from '../../componentes/tipos'
import { CARGOS_CON_DINERO } from '../../componentes/cargos'
import PaginaReporte from './PaginaReporte'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/reporte-financiero', element: <PaginaReporte /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/reporte-financiero',
    etiqueta: 'Reporte financiero',
    orden: 50,
    seccion: 'dinero',
    cargos: CARGOS_CON_DINERO,
    descripcion: 'Ingresos, gastos y balance por periodo',
  },
]
