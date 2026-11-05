// Comunicados (requiere sesión). Todo lo que depende del contrato del #33 está aquí.
//
// PENDIENTE de confirmar con el #33. Se propone (coincide con el PR de la API):
//   GET  /comunicados        → Comunicado[]   (solo los VIGENTES que mi cargo puede ver, el más reciente primero)
//   GET  /comunicados/{id}   → Comunicado
//   POST /comunicados        ← ComunicadoNuevo → Comunicado
//   PUT  /comunicados/{id}   ← ComunicadoNuevo → Comunicado
//   GET  /iglesias           → [{ id, nombre }]   (#12)
// `iglesia_id` vacío (null) significa "todo el Presbiterio": solo el presbítero lo publica (D20).
// Un comunicado no se borra: vence al pasar su `vigente_hasta`.
// Si el contrato cambia, solo se ajusta este archivo.

import { api } from './cliente'

export interface Comunicado {
  id: number
  titulo: string
  contenido: string
  /** null = todo el Presbiterio. */
  iglesia_id: number | null
  iglesia_nombre?: string | null
  /** Fecha y hora ISO con zona. */
  publicado_en: string
  /** "AAAA-MM-DD": último día en que se muestra. */
  vigente_hasta: string
  vigente: boolean
}

export interface ComunicadoNuevo {
  titulo: string
  contenido: string
  iglesia_id: number | null
  vigente_hasta: string
}

export interface IglesiaOpcion {
  id: number
  nombre: string
}

export function listarComunicados(): Promise<Comunicado[]> {
  return api.get<Comunicado[]>('/comunicados')
}

export function obtenerComunicado(id: number): Promise<Comunicado> {
  return api.get<Comunicado>(`/comunicados/${id}`)
}

export function publicarComunicado(datos: ComunicadoNuevo): Promise<Comunicado> {
  return api.post<Comunicado>('/comunicados', datos)
}

export function editarComunicado(id: number, datos: ComunicadoNuevo): Promise<Comunicado> {
  return api.put<Comunicado>(`/comunicados/${id}`, datos)
}

export function listarIglesiasParaComunicados(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}
