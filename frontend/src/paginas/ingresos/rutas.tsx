import type { ModuloRutas } from '../../componentes/tipos'
import FormularioIngresos from './FormularioIngresos'
import PaginaIngresos from './PaginaIngresos'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/ingresos', element: <PaginaIngresos /> },
  { path: '/ingresos/nuevo', element: <FormularioIngresos /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/ingresos',
    etiqueta: 'Ingresos',
    orden: 40,
    descripcion: 'Diezmos, ofrendas y EVAMI por culto',
  },
]
