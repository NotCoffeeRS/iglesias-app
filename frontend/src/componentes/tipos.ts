import type { ComponentType, ReactNode } from 'react'
import type { RouteObject } from 'react-router-dom'
import type { Cargo } from '../api/usuarios'

/** Un enlace del menú principal. */
export interface EntradaMenu {
  /** Ruta a la que lleva, p. ej. `/miembros`. */
  ruta: string
  /** Texto visible, p. ej. "Miembros". */
  etiqueta: string
  /** Menor número = más arriba. Sin orden va al final. */
  orden?: number
  /** Si se indica, el módulo aparece como acceso en el mosaico de Inicio con este texto. */
  descripcion?: string
  /** Cargos que ven esta entrada. Sin lista, la ven todos (el servidor valida el acceso de todos modos). */
  cargos?: readonly Cargo[]
}

/**
 * Lo que exporta cada `src/paginas/<modulo>/rutas.tsx`.
 * El enrutador de `App.tsx` lo descubre solo; no hay que registrarlo en ningún lado.
 */
export interface ModuloRutas {
  /** Rutas que se muestran dentro del layout (encabezado y menú). */
  rutas?: RouteObject[]
  /** Rutas a pantalla completa, sin layout (p. ej. el inicio de sesión). */
  rutasSinLayout?: RouteObject[]
  /** Enlaces que el módulo agrega al menú. */
  menu?: EntradaMenu[]
  /**
   * Componente que envuelve a todas las rutas con layout (p. ej. exigir sesión).
   * Las `rutasSinLayout` no pasan por él, así que ahí van las páginas públicas.
   */
  envoltorio?: ComponentType<{ children: ReactNode }>
}
