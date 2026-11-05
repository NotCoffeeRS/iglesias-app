// Eventos (requiere sesión). Todo lo que depende del contrato del #32 está aquí.
//
// PENDIENTE de confirmar con el #32. Se propone:
//   GET  /eventos?desde=AAAA-MM-DD[&iglesia_id=N] → Evento[]
//        (de esa fecha en adelante, ordenados por fecha y hora; incluye los cancelados, marcados)
//   GET  /eventos/{id}           → Evento
//   POST /eventos                ← EventoNuevo → Evento
//   PUT  /eventos/{id}           ← EventoNuevo → Evento
//   POST /eventos/{id}/cancelar  → Evento      (un evento no se borra: se cancela)
//   GET  /iglesias               → [{ id, nombre }]   (#12)
// `fecha` viaja como "AAAA-MM-DD" y `hora` como "HH:MM" (hora de Mérida, sin zona).
// `iglesia_id` vacío (null) significa "todo el Presbiterio": solo el presbítero lo crea (D20).
// Costo, inscripción y recordatorios NO se modelan: el Issue #32 dice que no se implementen.
// Si el contrato cambia, solo se ajusta este archivo.

import { api } from './cliente'

export interface Evento {
  id: number
  titulo: string
  fecha: string
  /** "HH:MM" o "HH:MM:SS". */
  hora: string
  /** null = todo el Presbiterio. */
  iglesia_id: number | null
  iglesia_nombre?: string | null
  lugar?: string | null
  descripcion?: string | null
  cancelado: boolean
}

export interface EventoNuevo {
  titulo: string
  fecha: string
  hora: string
  iglesia_id: number | null
  lugar?: string | null
  descripcion?: string | null
}

export interface IglesiaOpcion {
  id: number
  nombre: string
}

export function listarEventos(desde: string, iglesia_id?: number): Promise<Evento[]> {
  const filtro = iglesia_id ? `&iglesia_id=${iglesia_id}` : ''
  return api.get<Evento[]>(`/eventos?desde=${desde}${filtro}`)
}

export function obtenerEvento(id: number): Promise<Evento> {
  return api.get<Evento>(`/eventos/${id}`)
}

export function crearEvento(datos: EventoNuevo): Promise<Evento> {
  return api.post<Evento>('/eventos', datos)
}

export function editarEvento(id: number, datos: EventoNuevo): Promise<Evento> {
  return api.put<Evento>(`/eventos/${id}`, datos)
}

export function cancelarEvento(id: number): Promise<Evento> {
  return api.post<Evento>(`/eventos/${id}/cancelar`, {})
}

export function listarIglesiasParaEventos(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}
