// Íconos de línea (24×24) del menú y de los campos. Cada uno es una lista de trazos SVG.
// Se dibujan en `Icono.tsx` con el color del texto (`currentColor`).

export const ICONOS = {
  inicio: ['M3 11l9-8 9 8', 'M5 10v10h5v-6h4v6h5V10'],
  iglesia: ['M12 2v4', 'M10 4h4', 'M6 21V11l6-4 6 4v10', 'M3 21h18', 'M10 21v-5h4v5'],
  horarios: ['M12 7v5l3 2', 'M12 3a9 9 0 100 18 9 9 0 000-18Z'],
  miembros: ['M12 4a4 4 0 100 8 4 4 0 000-8Z', 'M4 21c0-4 3.6-6 8-6s8 2 8 6'],
  grupos: [
    'M9 4.5a3.5 3.5 0 100 7 3.5 3.5 0 000-7Z',
    'M2 20c0-3.5 3-5.5 7-5.5s7 2 7 5.5',
    'M17 6.5a2.5 2.5 0 110 5',
    'M18 14.7c2.4.4 4 1.9 4 4.3',
  ],
  menores: [
    'M12 3a9 9 0 100 18 9 9 0 000-18Z',
    'M8 14s1.5 2 4 2 4-2 4-2',
    'M9 9.5h.01',
    'M15 9.5h.01',
  ],
  usuarios: ['M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3Z', 'M9 12l2 2 4-4'],
  asignaciones: ['M7 7h13', 'M16 3l4 4-4 4', 'M17 17H4', 'M8 13l-4 4 4 4'],
  asistencia: [
    'M7 4h10a3 3 0 013 3v10a3 3 0 01-3 3H7a3 3 0 01-3-3V7a3 3 0 013-3Z',
    'M8.5 12l2.5 2.5 4.5-5',
  ],
  ingresos: ['M12 3a9 9 0 100 18 9 9 0 000-18Z', 'M12 7v10', 'M8 13l4 4 4-4'],
  gastos: ['M12 3a9 9 0 100 18 9 9 0 000-18Z', 'M12 17V7', 'M8 11l4-4 4 4'],
  reporte: ['M4 20V10', 'M10 20V4', 'M16 20v-7', 'M22 20H2'],
  eventos: [
    'M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2Z',
    'M3 10h18',
    'M8 3v4',
    'M16 3v4',
  ],
  comunicados: ['M3 10v4a1 1 0 001 1h2l7 4V5L6 9H4a1 1 0 00-1 1Z', 'M16 9a4 4 0 010 6'],
  buscar: ['M11 4a7 7 0 100 14 7 7 0 000-14Z', 'M20 20l-4-4'],
  flecha: ['M6 9l6 6 6-6'],
} as const

export type NombreIcono = keyof typeof ICONOS
