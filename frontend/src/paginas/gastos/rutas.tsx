import type { ModuloRutas } from '../../componentes/tipos'
import { CARGOS_CON_DINERO } from '../../componentes/cargos'
import FormularioGasto from './FormularioGasto'
import PaginaGastos from './PaginaGastos'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/gastos', element: <PaginaGastos /> },
  { path: '/gastos/nuevo', element: <FormularioGasto /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/gastos',
    etiqueta: 'Gastos',
    orden: 45,
    seccion: 'dinero',
    cargos: CARGOS_CON_DINERO,
    descripcion: 'Luz, agua, renta y más',
  },
]
