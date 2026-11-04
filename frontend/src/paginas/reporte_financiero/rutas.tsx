import type { ModuloRutas } from '../../componentes/tipos'
import PaginaReporte from './PaginaReporte'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/reporte-financiero', element: <PaginaReporte /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/reporte-financiero',
    etiqueta: 'Reporte financiero',
    orden: 50,
    descripcion: 'Ingresos, gastos y balance por periodo',
  },
]
