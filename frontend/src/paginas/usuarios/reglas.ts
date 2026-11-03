// Qué puede hacer cada cargo con las cuentas de usuario (decisiones D19 y D20).
//
// IMPORTANTE: esto solo decide qué opciones se MUESTRAN. El servidor vuelve a validar todo
// (AGENTS.md §4.10); si estas reglas y las del servidor difieren, gana el servidor (403).

import { CARGOS, type Cargo, type IglesiaOpcion, type Usuario, type Yo } from '../../api/usuarios'

/** Cargos con acceso al dinero (AGENTS.md §9). Nadie asigna un cargo con más dinero del que tiene. */
const CON_DINERO: Cargo[] = ['presbitero', 'pastor', 'tesorero']

/** Solo estos cargos crean y editan usuarios (criterio del #9). */
export function puedeGestionar(yo: Yo): boolean {
  return yo.cargo === 'presbitero' || yo.cargo === 'pastor' || yo.cargo === 'apoyo_pastor'
}

/**
 * Cargos que `yo` puede asignar al crear o editar a alguien.
 * - Nadie crea otro presbítero desde la app (D20, regla 7).
 * - Solo el presbítero crea pastores (D19).
 * - El apoyo del pastor solo crea cargos sin acceso al dinero (D19).
 */
export function cargosAsignables(yo: Yo): Cargo[] {
  const sinPresbitero = CARGOS.map((c) => c.clave).filter((c) => c !== 'presbitero')
  if (yo.cargo === 'presbitero') return sinPresbitero
  if (yo.cargo === 'pastor') return sinPresbitero.filter((c) => c !== 'pastor')
  if (yo.cargo === 'apoyo_pastor') return sinPresbitero.filter((c) => !CON_DINERO.includes(c))
  return []
}

/** El presbítero elige cualquier iglesia; pastor y apoyo solo la suya (D20, regla 5). */
export function iglesiasAsignables(yo: Yo, iglesias: IglesiaOpcion[]): IglesiaOpcion[] {
  if (yo.cargo === 'presbitero') return iglesias
  return iglesias.filter((i) => i.id === yo.iglesia_id)
}

/** ¿Puede `yo` abrir la edición de `objetivo`? Sin esto no se ofrece el formulario. */
export function puedeEditarA(
  yo: Yo,
  objetivo: Pick<Usuario, 'id' | 'cargo' | 'iglesia_id'>,
): boolean {
  if (!puedeGestionar(yo)) return false
  if (yo.cargo === 'presbitero') return true
  if (objetivo.iglesia_id !== yo.iglesia_id) return false
  // Cada quien puede corregir sus propios datos; a otros solo si su cargo es uno que puede asignar
  // (así el apoyo no toca a un tesorero ni a un pastor).
  return objetivo.id === yo.id || cargosAsignables(yo).includes(objetivo.cargo)
}

/** El cargo queda fijo en la propia cuenta (D20, regla 8) y cuando no se puede asignar. */
export function cargoBloqueado(yo: Yo, objetivo: Pick<Usuario, 'id' | 'cargo'>): boolean {
  return objetivo.id === yo.id || !cargosAsignables(yo).includes(objetivo.cargo)
}
