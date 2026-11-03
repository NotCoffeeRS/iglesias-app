// Ingresos por culto y tipo (requiere sesión; dinero: solo pastor, tesorero y presbítero).
// Todo lo que depende del contrato del #25 está aquí.
//
// PENDIENTE de confirmar con el #25. Se propone:
//   GET  /ingresos?desde=AAAA-MM-DD&hasta=AAAA-MM-DD[&iglesia_id=N] → Ingreso[]
//        (incluye los anulados, marcados; sin iglesia_id devuelve todas las de mi alcance)
//   POST /ingresos            ← IngresosNuevos → Ingreso[]   (una sola operación: todo o nada)
//   POST /ingresos/{id}/anular ← { motivo } → Ingreso         (no se borra; queda el motivo)
//   GET  /iglesias            → [{ id, nombre }]               (#12)
// Los montos viajan como TEXTO con dos decimales ("1500.50"), igual que NUMERIC(12,2) en la base,
// para evitar errores de redondeo. No existe ningún campo de persona (D17: no se registra quién dio).
// Si el contrato cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type TipoIngreso = 'diezmos' | 'ofrendas' | 'evami' | 'talento' | 'otras'
export type Culto = 'culto_domingo' | 'culto_entre_semana' | 'otro'

export interface Ingreso {
  id: number
  iglesia_id: number
  iglesia_nombre?: string | null
  fecha: string
  culto?: Culto | null
  tipo: TipoIngreso
  /** Texto con dos decimales ("1500.50"); se tolera también un número. */
  monto: string | number
  /** Obligatoria en "otras". */
  descripcion?: string | null
  anulado: boolean
  motivo_anulacion?: string | null
}

export interface Partida {
  tipo: TipoIngreso
  monto: string
  descripcion?: string | null
}

export interface IngresosNuevos {
  iglesia_id: number
  fecha: string
  culto?: Culto | null
  partidas: Partida[]
}

export interface IglesiaOpcion {
  id: number
  nombre: string
}

export interface Filtro {
  desde: string
  hasta: string
  /** Sin valor = todas las iglesias de mi alcance. */
  iglesia_id?: number
}

export function listarIngresos({ desde, hasta, iglesia_id }: Filtro): Promise<Ingreso[]> {
  const consulta = `desde=${desde}&hasta=${hasta}${iglesia_id ? `&iglesia_id=${iglesia_id}` : ''}`
  return api.get<Ingreso[]>(`/ingresos?${consulta}`)
}

export function registrarIngresos(datos: IngresosNuevos): Promise<Ingreso[]> {
  return api.post<Ingreso[]>('/ingresos', datos)
}

export function anularIngreso(id: number, motivo: string): Promise<Ingreso> {
  return api.post<Ingreso>(`/ingresos/${id}/anular`, { motivo })
}

export function listarIglesiasParaIngresos(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}

/** Lista cerrada de tipos (AGENTS.md §9 y D17). */
export const TIPOS: { clave: TipoIngreso; nombre: string; ayuda?: string }[] = [
  { clave: 'diezmos', nombre: 'Diezmos' },
  { clave: 'ofrendas', nombre: 'Ofrendas' },
  { clave: 'evami', nombre: 'EVAMI' },
  { clave: 'talento', nombre: 'Talento o venta de comida' },
  { clave: 'otras', nombre: 'Otras donaciones', ayuda: 'Describe de qué fueron.' },
]

export const CULTOS: { clave: Culto; nombre: string }[] = [
  { clave: 'culto_domingo', nombre: 'Culto de domingo' },
  { clave: 'culto_entre_semana', nombre: 'Culto entre semana' },
  { clave: 'otro', nombre: 'Otro culto' },
]
