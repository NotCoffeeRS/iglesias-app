import type { ModuloRutas } from '../../componentes/tipos'
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
    descripcion: 'Luz, agua, renta y más',
  },
]
