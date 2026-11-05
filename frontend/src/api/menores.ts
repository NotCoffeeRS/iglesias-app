// HU-25: menores y tutores, solo gestores de su iglesia; presbítero en todas.
import { api } from './cliente'

export type Sexo = 'femenino' | 'masculino'
export type Categoria = 'nino' | 'nina' | 'adolescente'
export interface Tutor {
  nombre: string
  telefono: string
}
export interface MenorEntrada {
  iglesia_id: number
  nombre: string
  fecha_nacimiento: string
  sexo: Sexo
  direccion: string
  activo: boolean
  tutores: Tutor[]
}
export interface MenorResumen {
  id: number
  iglesia_id: number
  iglesia_nombre: string
  nombre: string
  fecha_nacimiento: string
  sexo: Sexo
  edad: number
  categoria: Categoria | null
  activo: boolean
}
export interface Menor extends MenorResumen {
  direccion: string | null
  tutores: Tutor[]
}
export const listarMenores = () => api.get<MenorResumen[]>('/menores')
export const obtenerMenor = (id: number) => api.get<Menor>(`/menores/${id}`)
export const crearMenor = (datos: MenorEntrada) => api.post<Menor>('/menores', datos)
export const actualizarMenor = (id: number, datos: MenorEntrada) =>
  api.put<Menor>(`/menores/${id}`, datos)
export const listarIglesias = () => api.get<{ id: number; nombre: string }[]>('/iglesias')
