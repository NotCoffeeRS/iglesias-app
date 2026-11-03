import type { ModuloRutas } from '../../componentes/tipos'
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
    descripcion: 'Cuentas y cargos del liderazgo',
  },
]
