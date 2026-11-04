import type { ModuloRutas } from '../../componentes/tipos'
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
    descripcion: 'Registro y estado de cada miembro',
  },
]
