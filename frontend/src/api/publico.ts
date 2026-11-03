// Datos públicos (sin sesión): iglesias, sedes y horarios.
//
// PENDIENTE de confirmar con el #14 (y #12): el #14 no define un endpoint público. Se propone
// `GET /publico/iglesias` sin sesión y con esta forma. Si cambia, solo se ajusta este archivo.
//
// A propósito no se piden ni se muestran teléfonos personales (p. ej. del pastor): la página
// pública solo muestra el teléfono de la iglesia.

import { api } from './cliente'

const RUTA_PUBLICA = '/publico/iglesias'

export type TipoServicio =
  | 'culto_domingo'
  | 'culto_entre_semana'
  | 'oracion'
  | 'jovenes'
  | 'dna'
  | 'escuela_ibid'
  | 'celula'
  | 'ministerio'

export type DiaSemana =
  'domingo' | 'lunes' | 'martes' | 'miercoles' | 'jueves' | 'viernes' | 'sabado'

export interface HorarioPublico {
  id: number
  tipo: TipoServicio
  dia: DiaSemana
  /** "HH:MM" o "HH:MM:SS". */
  hora_inicio: string
  hora_fin?: string | null
  descripcion?: string | null
}

export interface SedePublica {
  id: number
  nombre: string
  direccion: string
  enlace_maps?: string | null
  horarios: HorarioPublico[]
}

export interface RedSocial {
  nombre: string
  url: string
}

export interface IglesiaPublica {
  id: number
  nombre: string
  pastor?: string | null
  foto_url?: string | null
  telefono_iglesia?: string | null
  redes: RedSocial[]
  sedes: SedePublica[]
}

export function obtenerIglesiasPublicas(): Promise<IglesiaPublica[]> {
  return api.get<IglesiaPublica[]>(RUTA_PUBLICA)
}

export const NOMBRES_TIPO: Record<TipoServicio, string> = {
  culto_domingo: 'Culto de domingo',
  culto_entre_semana: 'Culto entre semana',
  oracion: 'Oración',
  jovenes: 'Jóvenes',
  dna: 'DNA',
  escuela_ibid: 'Escuela (IBID)',
  celula: 'Célula',
  ministerio: 'Ministerio',
}

/** Orden de la semana para mostrar, empezando en domingo. */
export const DIAS: { clave: DiaSemana; nombre: string }[] = [
  { clave: 'domingo', nombre: 'Domingo' },
  { clave: 'lunes', nombre: 'Lunes' },
  { clave: 'martes', nombre: 'Martes' },
  { clave: 'miercoles', nombre: 'Miércoles' },
  { clave: 'jueves', nombre: 'Jueves' },
  { clave: 'viernes', nombre: 'Viernes' },
  { clave: 'sabado', nombre: 'Sábado' },
]
