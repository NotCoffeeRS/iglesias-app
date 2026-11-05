import type { ModuloRutas } from '../../componentes/tipos'
import { CARGOS_CON_MIEMBROS_Y_GRUPOS } from '../../componentes/cargos'
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
    seccion: 'personas',
    icono: 'grupos',
    cargos: CARGOS_CON_MIEMBROS_Y_GRUPOS,
    descripcion: 'Redes, células y ministerios con su líder',
  },
]
