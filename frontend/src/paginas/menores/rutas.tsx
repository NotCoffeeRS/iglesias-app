import type { ModuloRutas } from '../../componentes/tipos'
import FormularioMenor from './FormularioMenor'
import ListaMenores from './ListaMenores'

export const rutas: ModuloRutas['rutas'] = [
  { path: '/menores', element: <ListaMenores /> },
  { path: '/menores/nuevo', element: <FormularioMenor /> },
  { path: '/menores/:id/editar', element: <FormularioMenor /> },
]
export const menu: ModuloRutas['menu'] = [
  {
    ruta: '/menores',
    etiqueta: 'Niños y adolescentes',
    orden: 25,
    seccion: 'personas',
    icono: 'menores',
    cargos: ['presbitero', 'pastor', 'apoyo_pastor'],
    descripcion: 'Registro de menores y sus tutores',
  },
]
