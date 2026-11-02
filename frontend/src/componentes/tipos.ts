import type { RouteObject } from 'react-router-dom'

/** Un enlace del menú principal. */
export interface EntradaMenu {
  /** Ruta a la que lleva, p. ej. `/miembros`. */
  ruta: string
  /** Texto visible, p. ej. "Miembros". */
  etiqueta: string
  /** Menor número = más arriba. Sin orden va al final. */
  orden?: number
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
}
