import type { ModuloRutas } from '../../componentes/tipos'
import FormularioGrupo from './FormularioGrupo'
import ListaGrupos from './ListaGrupos'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/grupos', element: <ListaGrupos /> },
  { path: '/grupos/nuevo', element: <FormularioGrupo /> },
  { path: '/grupos/:id/editar', element: <FormularioGrupo /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/grupos',
    etiqueta: 'Grupos',
    orden: 25,
    descripcion: 'Redes, células y ministerios con su líder',
  },
]
