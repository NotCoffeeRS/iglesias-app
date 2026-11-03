import type { ModuloRutas } from '../../componentes/tipos'
import HorariosPublicos from './HorariosPublicos'

// Página pública: va en rutasSinLayout para no exigir sesión.
export const rutasSinLayout: ModuloRutas['rutasSinLayout'] = [
  { path: '/ubicaciones', element: <HorariosPublicos /> },
]
