import type { ModuloRutas } from '../../componentes/tipos'
import CerrarSesion from './CerrarSesion'
import Login from './Login'
import PaginaPerfil from './PaginaPerfil'
import RequiereSesion from './RequiereSesion'

// Todas las rutas con layout exigen sesión; las públicas van en rutasSinLayout de su módulo.
export const envoltorio: ModuloRutas['envoltorio'] = RequiereSesion

// «Mi perfil» va dentro del layout. «Cerrar sesión» ya no es una entrada del menú de
// pantallas: vive en el bloque «Mi cuenta» del pie del menú y pide confirmación.
export const rutas: ModuloRutas['rutas'] = [{ path: '/perfil', element: <PaginaPerfil /> }]

export const rutasSinLayout: ModuloRutas['rutasSinLayout'] = [
  { path: '/login', element: <Login /> },
  { path: '/salir', element: <CerrarSesion /> },
]
