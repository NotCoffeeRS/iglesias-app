// Grupos: redes, células, ministerios, escuelas y áreas (requiere sesión).
// Todo lo que depende del contrato del #20 está aquí.
//
// PENDIENTE de confirmar con el #20. Se propone:
//   GET  /grupos[?tipo=]               → GrupoResumen[]  (solo los del alcance del usuario)
//   GET  /grupos/{id}                  → Grupo
//   POST /grupos                       ← GrupoEntrada → Grupo
//   PUT  /grupos/{id}                  ← GrupoEntrada → Grupo
//   GET  /iglesias                     → [{ id, nombre }]                  (#12)
//   GET  /miembros?iglesia_id={id}     → [{ id, nombre, ... }]            (#17; candidatos a líder)
// Si cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type TipoGrupo = 'red' | 'celula' | 'ministerio' | 'escuela' | 'area'

export interface GrupoResumen {
  id: number
  nombre: string
  tipo: TipoGrupo
  iglesia_nombre: string
  lider_nombre?: string | null
  asistente_nombre?: string | null
}

export interface Grupo {
  id: number
  nombre: string
  tipo: TipoGrupo
  iglesia_id: number
  /** Id del miembro que lo dirige. */
  lider_id: number
  /** Id del miembro asistente o segundo al mando (opcional). */
  asistente_id?: number | null
}

export type GrupoEntrada = Omit<Grupo, 'id'>

export interface Opcion {
  id: number
  nombre: string
}

export function listarGrupos(tipo?: TipoGrupo): Promise<GrupoResumen[]> {
  return api.get<GrupoResumen[]>(tipo ? `/grupos?tipo=${tipo}` : '/grupos')
}

export function obtenerGrupo(id: number): Promise<Grupo> {
  return api.get<Grupo>(`/grupos/${id}`)
}

export function crearGrupo(datos: GrupoEntrada): Promise<Grupo> {
  return api.post<Grupo>('/grupos', datos)
}

export function actualizarGrupo(id: number, datos: GrupoEntrada): Promise<Grupo> {
  return api.put<Grupo>(`/grupos/${id}`, datos)
}

export function listarIglesiasParaGrupos(): Promise<Opcion[]> {
  return api.get<Opcion[]>('/iglesias')
}

export function listarCandidatos(iglesiaId: number): Promise<Opcion[]> {
  return api.get<Opcion[]>(`/miembros?iglesia_id=${iglesiaId}`)
}

export const TIPOS_GRUPO: { clave: TipoGrupo; nombre: string; plural: string; ejemplo: string }[] =
  [
    { clave: 'red', nombre: 'Red', plural: 'Redes', ejemplo: 'Varones, Damas, Jóvenes' },
    { clave: 'celula', nombre: 'Célula', plural: 'Células', ejemplo: 'Célula Norte' },
    { clave: 'ministerio', nombre: 'Ministerio', plural: 'Ministerios', ejemplo: 'Alabanza' },
    { clave: 'escuela', nombre: 'Escuela', plural: 'Escuelas', ejemplo: 'IBID' },
    { clave: 'area', nombre: 'Área', plural: 'Áreas', ejemplo: 'La tiendita' },
  ]
