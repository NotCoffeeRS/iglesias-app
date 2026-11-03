// Iglesias, sedes y redes sociales (requiere sesión). Todo lo que depende del contrato del #12 está aquí.
//
// PENDIENTE de confirmar con el #12. Se propone:
//   GET /iglesias        → IglesiaResumen[]  (solo las que el usuario puede ver)
//   GET /iglesias/{id}   → Iglesia
//   PUT /iglesias/{id}   ← IglesiaEntrada → Iglesia  (el servidor valida quién puede editar)
// Si cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type TipoRed = 'propia' | 'relacionada'

export interface RedSocial {
  id?: number
  nombre: string
  url: string
  tipo: TipoRed
}

export interface Sede {
  id?: number
  nombre: string
  direccion: string
  enlace_maps?: string | null
}

export interface Iglesia {
  id: number
  nombre: string
  foto_url?: string | null
  pastor?: string | null
  telefono_pastor?: string | null
  telefono_iglesia?: string | null
  redes: RedSocial[]
  sedes: Sede[]
}

export interface IglesiaResumen {
  id: number
  nombre: string
  pastor?: string | null
  foto_url?: string | null
  total_sedes: number
}

export type IglesiaEntrada = Omit<Iglesia, 'id'>

export function listarIglesias(): Promise<IglesiaResumen[]> {
  return api.get<IglesiaResumen[]>('/iglesias')
}

export function obtenerIglesia(id: number): Promise<Iglesia> {
  return api.get<Iglesia>(`/iglesias/${id}`)
}

export function actualizarIglesia(id: number, datos: IglesiaEntrada): Promise<Iglesia> {
  return api.put<Iglesia>(`/iglesias/${id}`, datos)
}
