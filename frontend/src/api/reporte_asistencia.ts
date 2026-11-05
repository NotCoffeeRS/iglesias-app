import { api } from './cliente'

export interface Totales {
  registros: number
  asistencias: number
  faltas: number
}
export interface Detalle extends Totales {
  fecha: string
  servicio: string
}
export interface IglesiaReporte extends Totales {
  iglesia_id: number
  iglesia_nombre: string
  detalle: Detalle[]
}
export interface Reporte {
  desde: string
  hasta: string
  servicio: string | null
  totales: Totales
  iglesias: IglesiaReporte[]
}
export interface Filtro {
  desde: string
  hasta: string
  iglesia_id?: number
  servicio?: string
}
export function obtenerReporte(f: Filtro): Promise<Reporte> {
  const q = new URLSearchParams({ desde: f.desde, hasta: f.hasta })
  if (f.iglesia_id) q.set('iglesia_id', String(f.iglesia_id))
  if (f.servicio) q.set('servicio', f.servicio)
  return api.get<Reporte>(`/reportes/asistencia?${q}`)
}
export const listarIglesias = () => api.get<{ id: number; nombre: string }[]>('/iglesias')
export const SERVICIOS = [
  ['culto_domingo', 'Culto de domingo'],
  ['culto_entre_semana', 'Culto entre semana'],
  ['oracion', 'Oración'],
  ['jovenes', 'Jóvenes'],
  ['dna', 'DNA'],
  ['escuela_ibid', 'Escuela IBID'],
  ['celula', 'Célula'],
  ['ministerio', 'Ministerio'],
  ['otro', 'Otro'],
] as const
