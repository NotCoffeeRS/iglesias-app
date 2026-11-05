// Qué cargos ven cada módulo en el menú y en el Inicio (AGENTS.md §9, D9, D19, D20 y D22).
//
// IMPORTANTE: esto solo decide qué se MUESTRA. El servidor vuelve a validar todo
// (AGENTS.md §4.10); si estas listas y las del servidor difieren, gana el servidor (403).

import { CARGOS, type Cargo } from '../api/usuarios'

/** Dinero (ingresos, gastos y reporte financiero): pastor y tesorero de su iglesia, y el presbítero. */
export const CARGOS_CON_DINERO: Cargo[] = ['presbitero', 'pastor', 'tesorero']

/** Crean y editan cuentas de usuario. */
export const CARGOS_QUE_GESTIONAN_USUARIOS: Cargo[] = ['presbitero', 'pastor', 'apoyo_pastor']

/** Marcan asistencia: el líder de célula y el ujier en turno (D16). */
export const CARGOS_QUE_MARCAN_ASISTENCIA: Cargo[] = ['lider_celula', 'ujier']

/** Ven miembros y grupos: todos menos el tesorero (D20) y el ujier, que solo marca faltas. */
export const CARGOS_CON_MIEMBROS_Y_GRUPOS: Cargo[] = CARGOS.map((c) => c.clave).filter(
  (c) => c !== 'tesorero' && c !== 'ujier',
)
