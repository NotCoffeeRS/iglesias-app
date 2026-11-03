// Miembros (requiere sesión). Todo lo que depende del contrato del #17 está aquí.
//
// PENDIENTE de confirmar con el #17. Se propone:
//   GET  /miembros[?estado=]  → MiembroResumen[]  (solo los del alcance del usuario)
//   GET  /miembros/{id}       → Miembro
//   POST /miembros            ← MiembroEntrada → Miembro
//   PUT  /miembros/{id}       ← MiembroEntrada → Miembro
//   GET  /iglesias            → [{ id, nombre }]  (#12; para elegir iglesia al registrar)
// La búsqueda por nombre se hace en el navegador para no poner nombres en las URLs (AGENTS.md §4.9).
// Si cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type EstadoMiembro =
  | 'activo'
  | 'inactivo'
  | 'visitante'
  | 'en_proceso_ganar'
  | 'en_proceso_discipular'
  | 'en_proceso_consolidar'

export type EstadoCivil = 'soltero' | 'casado' | 'union_libre' | 'divorciado' | 'viudo'

export interface MiembroResumen {
  id: number
  nombre: string
  telefono?: string | null
  estado: EstadoMiembro
  iglesia_nombre: string
}

export interface Miembro {
  id: number
  nombre: string
  telefono?: string | null
  correo?: string | null
  fecha_nacimiento?: string | null
  direccion?: string | null
  estado_civil?: EstadoCivil | null
  fecha_bautizo?: string | null
  fecha_ingreso?: string | null
  iglesia_id: number
  estado: EstadoMiembro
}

export type MiembroEntrada = Omit<Miembro, 'id'>

export interface IglesiaOpcion {
  id: number
  nombre: string
}

export function listarMiembros(estado?: EstadoMiembro): Promise<MiembroResumen[]> {
  return api.get<MiembroResumen[]>(estado ? `/miembros?estado=${estado}` : '/miembros')
}

export function obtenerMiembro(id: number): Promise<Miembro> {
  return api.get<Miembro>(`/miembros/${id}`)
}

export function crearMiembro(datos: MiembroEntrada): Promise<Miembro> {
  return api.post<Miembro>('/miembros', datos)
}

export function actualizarMiembro(id: number, datos: MiembroEntrada): Promise<Miembro> {
  return api.put<Miembro>(`/miembros/${id}`, datos)
}

export function listarIglesiasParaMiembros(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}

export const ESTADOS: { clave: EstadoMiembro; nombre: string }[] = [
  { clave: 'activo', nombre: 'Activo' },
  { clave: 'visitante', nombre: 'Visitante' },
  { clave: 'en_proceso_ganar', nombre: 'En proceso de ganar' },
  { clave: 'en_proceso_consolidar', nombre: 'En proceso de consolidar' },
  { clave: 'en_proceso_discipular', nombre: 'En proceso de discipular' },
  { clave: 'inactivo', nombre: 'Inactivo' },
]

export const ESTADOS_CIVILES: { clave: EstadoCivil; nombre: string }[] = [
  { clave: 'soltero', nombre: 'Soltero(a)' },
  { clave: 'casado', nombre: 'Casado(a)' },
  { clave: 'union_libre', nombre: 'Unión libre' },
  { clave: 'divorciado', nombre: 'Divorciado(a)' },
  { clave: 'viudo', nombre: 'Viudo(a)' },
]
