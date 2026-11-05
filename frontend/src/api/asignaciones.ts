// HU-14: gestores agregan; los líderes solo quitan integrantes de sus propios grupos.
import { api } from './cliente'

export interface GrupoAsignaciones {
  id: number
  nombre: string
  tipo: string
  iglesia_id: number
  iglesia_nombre: string
  activo: boolean
}
export interface MiembroAsignacion {
  id: number
  nombre: string
  estado: string
}
export const listarGrupos = () => api.get<GrupoAsignaciones[]>('/asignaciones/grupos')
export const listarIntegrantes = (grupo: number) =>
  api.get<MiembroAsignacion[]>(`/asignaciones/${grupo}`)
export const listarCandidatos = (grupo: number) =>
  api.get<MiembroAsignacion[]>(`/asignaciones/${grupo}/candidatos`)
export const asignarMiembro = (grupo_id: number, miembro_id: number) =>
  api.post<{ grupo_id: number; miembro_id: number }>('/asignaciones', { grupo_id, miembro_id })
export const quitarMiembro = (grupo: number, miembro: number) =>
  api.delete<void>(`/asignaciones/${grupo}/${miembro}`)
