// Usuarios, cargos y permisos (requiere sesión). Todo lo que depende del contrato del #9 está aquí.
//
// PENDIENTE de confirmar con el #9. Se propone:
//   GET  /usuarios/yo       → Yo                (quién soy: cargo e iglesia, para ocultar opciones)
//   GET  /usuarios          → UsuarioResumen[]  (solo los de mi alcance)
//   GET  /usuarios/{id}     → Usuario
//   POST /usuarios          ← UsuarioNuevo → Usuario
//   PUT  /usuarios/{id}     ← UsuarioCambios → Usuario
//   GET  /iglesias          → [{ id, nombre }]  (#12)
// Los usuarios no se borran: se desactivan (`activo`). La contraseña solo viaja al crear la cuenta.
// El servidor valida todo (D19, D20); la pantalla solo oculta lo que el cargo no puede usar.
// Si el contrato cambia, solo se ajusta este archivo.

import { api } from './cliente'

export type Cargo =
  | 'presbitero'
  | 'pastor'
  | 'esposa_pastor'
  | 'apoyo_pastor'
  | 'tesorero'
  | 'lider_red'
  | 'lider_celula'
  | 'lider_ministerio'
  | 'asistente'
  | 'diacono'
  | 'ministro'
  | 'encargado_area'
  | 'ujier'

/** Quién está usando la aplicación. */
export interface Yo {
  id: number
  nombre_completo: string
  cargo: Cargo
  /** null solo para el presbítero, que ve todas las iglesias. */
  iglesia_id: number | null
}

export interface UsuarioResumen {
  id: number
  nombre_usuario: string
  nombre_completo: string
  cargo: Cargo
  iglesia_id: number | null
  iglesia_nombre?: string | null
  activo: boolean
}

export interface Usuario {
  id: number
  nombre_usuario: string
  nombre_completo: string
  cargo: Cargo
  iglesia_id: number | null
  activo: boolean
}

export interface UsuarioNuevo {
  nombre_usuario: string
  nombre_completo: string
  cargo: Cargo
  iglesia_id: number
  contrasena: string
}

export interface UsuarioCambios {
  nombre_completo: string
  cargo: Cargo
  iglesia_id: number | null
  activo: boolean
}

export interface IglesiaOpcion {
  id: number
  nombre: string
}

export function obtenerYo(): Promise<Yo> {
  return api.get<Yo>('/usuarios/yo')
}

export function listarUsuarios(): Promise<UsuarioResumen[]> {
  return api.get<UsuarioResumen[]>('/usuarios')
}

export function obtenerUsuario(id: number): Promise<Usuario> {
  return api.get<Usuario>(`/usuarios/${id}`)
}

export function crearUsuario(datos: UsuarioNuevo): Promise<Usuario> {
  return api.post<Usuario>('/usuarios', datos)
}

export function actualizarUsuario(id: number, datos: UsuarioCambios): Promise<Usuario> {
  return api.put<Usuario>(`/usuarios/${id}`, datos)
}

export function listarIglesiasParaUsuarios(): Promise<IglesiaOpcion[]> {
  return api.get<IglesiaOpcion[]>('/iglesias')
}

/** Lista cerrada de cargos (AGENTS.md §9 y modelo de usuarios del #4). */
export const CARGOS: { clave: Cargo; nombre: string }[] = [
  { clave: 'presbitero', nombre: 'Presbítero' },
  { clave: 'pastor', nombre: 'Pastor' },
  { clave: 'esposa_pastor', nombre: 'Esposa de pastor' },
  { clave: 'apoyo_pastor', nombre: 'Apoyo del pastor' },
  { clave: 'tesorero', nombre: 'Tesorero' },
  { clave: 'lider_red', nombre: 'Líder de red' },
  { clave: 'lider_celula', nombre: 'Líder de célula' },
  { clave: 'lider_ministerio', nombre: 'Líder de ministerio' },
  { clave: 'asistente', nombre: 'Asistente' },
  { clave: 'diacono', nombre: 'Diácono' },
  { clave: 'ministro', nombre: 'Ministro' },
  { clave: 'encargado_area', nombre: 'Encargado de área' },
  { clave: 'ujier', nombre: 'Ujier' },
]
