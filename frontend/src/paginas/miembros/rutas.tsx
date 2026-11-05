import type { ModuloRutas } from '../../componentes/tipos'
import { CARGOS_CON_MIEMBROS_Y_GRUPOS } from '../../componentes/cargos'
import FormularioMiembro from './FormularioMiembro'
import ListaMiembros from './ListaMiembros'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/miembros', element: <ListaMiembros /> },
  { path: '/miembros/nuevo', element: <FormularioMiembro /> },
  { path: '/miembros/:id/editar', element: <FormularioMiembro /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/miembros',
    etiqueta: 'Miembros',
    orden: 20,
    cargos: CARGOS_CON_MIEMBROS_Y_GRUPOS,
    descripcion: 'Registro y estado de cada miembro',
  },
]
