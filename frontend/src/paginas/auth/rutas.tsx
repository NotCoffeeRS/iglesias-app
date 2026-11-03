import type { ModuloRutas } from '../../componentes/tipos'
import CerrarSesion from './CerrarSesion'
import Login from './Login'
import RequiereSesion from './RequiereSesion'

// Todas las rutas con layout exigen sesión; las públicas van en rutasSinLayout de su módulo.
export const envoltorio: ModuloRutas['envoltorio'] = RequiereSesion

export const rutasSinLayout: ModuloRutas['rutasSinLayout'] = [
  { path: '/login', element: <Login /> },
  { path: '/salir', element: <CerrarSesion /> },
]

export const menu: ModuloRutas['menu'] = [
  { ruta: '/salir', etiqueta: 'Cerrar sesión', orden: 1000 },
]
