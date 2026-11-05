import type { ModuloRutas } from '../../componentes/tipos'
import { CARGOS_QUE_GESTIONAN_USUARIOS } from '../../componentes/cargos'
import FormularioUsuario from './FormularioUsuario'
import ListaUsuarios from './ListaUsuarios'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/usuarios', element: <ListaUsuarios /> },
  { path: '/usuarios/nuevo', element: <FormularioUsuario /> },
  { path: '/usuarios/:id/editar', element: <FormularioUsuario /> },
]

export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/usuarios',
    etiqueta: 'Usuarios',
    orden: 30,
    seccion: 'personas',
    cargos: CARGOS_QUE_GESTIONAN_USUARIOS,
    descripcion: 'Cuentas y cargos del liderazgo',
  },
]
