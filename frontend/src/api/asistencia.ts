// Asistencia a los cultos (requiere sesión). Todo lo que depende del contrato del #23 está aquí.
//
// Reglas del #23: el líder de célula marca quién de su célula ASISTIÓ; el ujier (cargo rotativo)
// marca quién FALTÓ de quienes no tienen célula. Nadie se marca dos veces el mismo día y servicio.
//
// PENDIENTE de confirmar con el #23. Se propone:
//   GET /asistencia?fecha=AAAA-MM-DD&servicio=…  → HojaAsistencia[]
//       Una hoja por cada lista que el usuario puede marcar (su célula, y/o "sin célula" si es ujier).
//   PUT /asistencia  ← { fecha, servicio, hoja, marcados: number[] } → HojaAsistencia
//       Reemplaza las marcas de esa hoja, fecha y servicio (así no hay marcas duplicadas).
// Si cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type Servicio = 'culto_domingo' | 'culto_entre_semana' | 'otro'

/** "asistencias": se marca a quien asistió (líder de célula). "faltas": a quien faltó (ujier). */
export type ModoHoja = 'asistencias' | 'faltas'

export interface PersonaHoja {
  miembro_id: number
  nombre: string
  marcado: boolean
}

export interface HojaAsistencia {
  /** Identifica la lista, p. ej. "celula:5" o "sin_celula:2". */
  hoja: string
  modo: ModoHoja
  /** Lo que se muestra, p. ej. "Célula Norte" o "Sin célula". */
  titulo: string
  /** true si ya se guardó antes para esta fecha y servicio. */
  guardada: boolean
  personas: PersonaHoja[]
}

export function obtenerHojas(fecha: string, servicio: Servicio): Promise<HojaAsistencia[]> {
  return api.get<HojaAsistencia[]>(`/asistencia?fecha=${fecha}&servicio=${servicio}`)
}

export function guardarHoja(
  fecha: string,
  servicio: Servicio,
  hoja: string,
  marcados: number[],
): Promise<HojaAsistencia> {
  return api.put<HojaAsistencia>('/asistencia', { fecha, servicio, hoja, marcados })
}

export const SERVICIOS: { clave: Servicio; nombre: string }[] = [
  { clave: 'culto_domingo', nombre: 'Domingo' },
  { clave: 'culto_entre_semana', nombre: 'Entre semana' },
  { clave: 'otro', nombre: 'Otro' },
]
