// Reporte financiero: ingresos, gastos y balance por iglesia y periodo (requiere sesión;
// dinero: solo pastor, tesorero y presbítero). Todo lo que depende del contrato del #29 está aquí.
//
// PENDIENTE de confirmar con el #29. Se propone:
//   GET /reportes/financiero?desde=AAAA-MM-DD&hasta=AAAA-MM-DD[&iglesia_id=N] → Reporte
//     - `iglesias`: una entrada por cada iglesia de mi alcance (o solo la pedida).
//     - `consolidado`: solo lo recibe el presbítero y solo cuando no pide una iglesia concreta.
//     - Los ingresos y gastos anulados NO cuentan; el servidor ya los excluye.
//   GET /iglesias → [{ id, nombre }]   (#12)
// Los montos viajan como TEXTO con dos decimales ("1500.50"; el balance puede ser negativo),
// igual que NUMERIC(12,2) en la base, para evitar errores de redondeo.
// Si el contrato cambia, solo se ajusta este archivo.

import { api } from './cliente'

/** Una partida del desglose: p. ej. { clave: 'diezmos', monto: '1500.50' }. */
export interface Partida {
  clave: string
  /** Nombre para mostrar; si el servidor no lo manda, se usa la etiqueta local o la clave. */
  nombre?: string | null
  monto: string | number
}

export interface Resumen {
  ingresos: string | number
  gastos: string | number
  /** Ingresos menos gastos, sin anulados. Puede ser negativo. */
  balance: string | number
  ingresos_por_tipo: Partida[]
  gastos_por_categoria: Partida[]
}

export interface ResumenIglesia extends Resumen {
  iglesia_id: number
  iglesia_nombre: string
}

export interface Reporte {
  desde: string
  hasta: string
  consolidado?: Resumen | null
  iglesias: ResumenIglesia[]
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

export function obtenerReporte({ desde, hasta, iglesia_id }: Filtro): Promise<Reporte> {
  const consulta = `desde=${desde}&hasta=${hasta}${iglesia_id ? `&iglesia_id=${iglesia_id}` : ''}`
  return api.get<Reporte>(`/reportes/financiero?${consulta}`)
}

export function listarIglesiasParaReporte(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}

/** Etiquetas de las claves conocidas (tipos de ingreso de D17 y categorías de gasto de D18). */
export const ETIQUETAS: Record<string, string> = {
  diezmos: 'Diezmos',
  ofrendas: 'Ofrendas',
  evami: 'EVAMI',
  talento: 'Talento o venta de comida',
  otras: 'Otras donaciones',
  luz: 'Luz',
  agua: 'Agua',
  renta: 'Renta',
  mantenimiento: 'Mantenimiento',
  material_construccion: 'Material de construcción',
  materiales_reposiciones: 'Materiales y reposiciones',
  apoyo_miembros: 'Apoyo a miembros',
  otros: 'Otros',
}
