// Horarios de cada sede (requiere sesión). Todo lo que depende del contrato del #14 está aquí.
//
// PENDIENTE de confirmar con el #14. Se propone:
//   GET    /sedes                   → SedeResumen[]  (solo las que el usuario puede editar)
//   GET    /sedes/{id}/horarios     → Horario[]
//   POST   /sedes/{id}/horarios     ← HorarioEntrada → Horario
//   PUT    /horarios/{id}           ← HorarioEntrada → Horario
//   DELETE /horarios/{id}
// Si cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type TipoServicio =
  | 'culto_domingo'
  | 'culto_entre_semana'
  | 'oracion'
  | 'jovenes'
  | 'dna'
  | 'escuela_ibid'
  | 'celula'
  | 'ministerio'

export type DiaSemana =
  'domingo' | 'lunes' | 'martes' | 'miercoles' | 'jueves' | 'viernes' | 'sabado'

export interface SedeResumen {
  id: number
  nombre: string
  iglesia_nombre: string
}

export interface Horario {
  id: number
  tipo: TipoServicio
  dia: DiaSemana
  /** "HH:MM" o "HH:MM:SS". */
  hora_inicio: string
  hora_fin?: string | null
  descripcion?: string | null
}

export type HorarioEntrada = Omit<Horario, 'id'>

export function listarSedes(): Promise<SedeResumen[]> {
  return api.get<SedeResumen[]>('/sedes')
}

export function listarHorarios(sedeId: number): Promise<Horario[]> {
  return api.get<Horario[]>(`/sedes/${sedeId}/horarios`)
}

export function crearHorario(sedeId: number, datos: HorarioEntrada): Promise<Horario> {
  return api.post<Horario>(`/sedes/${sedeId}/horarios`, datos)
}

export function actualizarHorario(id: number, datos: HorarioEntrada): Promise<Horario> {
  return api.put<Horario>(`/horarios/${id}`, datos)
}

export function eliminarHorario(id: number): Promise<void> {
  return api.delete<void>(`/horarios/${id}`)
}

/** La lista cerrada de tipos (los únicos que acepta el servidor). */
export const TIPOS: { clave: TipoServicio; nombre: string }[] = [
  { clave: 'culto_domingo', nombre: 'Culto de domingo' },
  { clave: 'culto_entre_semana', nombre: 'Culto entre semana' },
  { clave: 'oracion', nombre: 'Oración' },
  { clave: 'jovenes', nombre: 'Jóvenes' },
  { clave: 'dna', nombre: 'DNA' },
  { clave: 'escuela_ibid', nombre: 'Escuela (IBID)' },
  { clave: 'celula', nombre: 'Célula' },
  { clave: 'ministerio', nombre: 'Ministerio' },
]

/** Orden de la semana, empezando en domingo. */
export const DIAS: { clave: DiaSemana; nombre: string }[] = [
  { clave: 'domingo', nombre: 'Domingo' },
  { clave: 'lunes', nombre: 'Lunes' },
  { clave: 'martes', nombre: 'Martes' },
  { clave: 'miercoles', nombre: 'Miércoles' },
  { clave: 'jueves', nombre: 'Jueves' },
  { clave: 'viernes', nombre: 'Viernes' },
  { clave: 'sabado', nombre: 'Sábado' },
]
