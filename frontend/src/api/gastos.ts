// Gastos con categorías fijas (requiere sesión; dinero: solo pastor, tesorero y presbítero).
// Todo lo que depende del contrato del #27 está aquí.
//
// PENDIENTE de confirmar con el #27. Se propone:
//   GET  /gastos?desde=AAAA-MM-DD&hasta=AAAA-MM-DD[&iglesia_id=N] → Gasto[]
//        (incluye los anulados, marcados; sin iglesia_id devuelve todas las de mi alcance)
//   POST /gastos              ← GastoNuevo → Gasto
//   POST /gastos/{id}/anular  ← { motivo } → Gasto      (no se borra; queda el motivo)
//   GET  /iglesias            → [{ id, nombre }]          (#12)
// Los montos viajan como TEXTO con dos decimales ("1500.50"), igual que NUMERIC(12,2) en la base,
// para evitar errores de redondeo.
// Si el contrato cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type Categoria =
  | 'luz'
  | 'agua'
  | 'renta'
  | 'mantenimiento'
  | 'material_construccion'
  | 'materiales_reposiciones'
  | 'apoyo_miembros'
  | 'otros'

export interface Gasto {
  id: number
  iglesia_id: number
  iglesia_nombre?: string | null
  fecha: string
  categoria: Categoria
  /** Texto con dos decimales ("1500.50"); se tolera también un número. */
  monto: string | number
  nota?: string | null
  anulado: boolean
  motivo_anulacion?: string | null
}

export interface GastoNuevo {
  iglesia_id: number
  fecha: string
  categoria: Categoria
  monto: string
  nota?: string | null
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

export function listarGastos({ desde, hasta, iglesia_id }: Filtro): Promise<Gasto[]> {
  const consulta = `desde=${desde}&hasta=${hasta}${iglesia_id ? `&iglesia_id=${iglesia_id}` : ''}`
  return api.get<Gasto[]>(`/gastos?${consulta}`)
}

export function registrarGasto(datos: GastoNuevo): Promise<Gasto> {
  return api.post<Gasto>('/gastos', datos)
}

export function anularGasto(id: number, motivo: string): Promise<Gasto> {
  return api.post<Gasto>(`/gastos/${id}/anular`, { motivo })
}

export function listarIglesiasParaGastos(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}

/** Lista cerrada de categorías (AGENTS.md §9 y D18). */
export const CATEGORIAS: { clave: Categoria; nombre: string }[] = [
  { clave: 'luz', nombre: 'Luz' },
  { clave: 'agua', nombre: 'Agua' },
  { clave: 'renta', nombre: 'Renta' },
  { clave: 'mantenimiento', nombre: 'Mantenimiento' },
  { clave: 'material_construccion', nombre: 'Material de construcción' },
  { clave: 'materiales_reposiciones', nombre: 'Materiales y reposiciones' },
  { clave: 'apoyo_miembros', nombre: 'Apoyo a miembros' },
  { clave: 'otros', nombre: 'Otros' },
]
