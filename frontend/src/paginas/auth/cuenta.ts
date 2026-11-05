import { useEffect, useState } from 'react'
import { listarIglesias } from '../../api/iglesias'
import { CARGOS, obtenerYo, type Yo } from '../../api/usuarios'

export function nombreDelCargo(cargo: string): string {
  return CARGOS.find((c) => c.clave === cargo)?.nombre ?? cargo
}

export interface Cuenta {
  yo: Yo
  /** Nombre de la iglesia, o null si la persona ve todas (presbítero). */
  iglesia: string | null
}

/** Quién está usando la app: nombre, cargo e iglesia. `null` mientras carga o si falla. */
export function useCuenta(): Cuenta | null {
  const [cuenta, setCuenta] = useState<Cuenta | null>(null)

  useEffect(() => {
    let vigente = true
    obtenerYo()
      .then(async (yo) => {
        let iglesia: string | null = null
        if (yo.iglesia_id !== null) {
          const iglesias = await listarIglesias().catch(() => [])
          iglesia = iglesias.find((i) => i.id === yo.iglesia_id)?.nombre ?? null
        }
        if (vigente) setCuenta({ yo, iglesia })
      })
      .catch(() => undefined)
    return () => {
      vigente = false
    }
  }, [])

  return cuenta
}

export function textoCargoEIglesia(cuenta: Cuenta): string {
  const lugar = cuenta.yo.iglesia_id === null ? 'Todas las iglesias' : cuenta.iglesia
  return lugar ? `${nombreDelCargo(cuenta.yo.cargo)} · ${lugar}` : nombreDelCargo(cuenta.yo.cargo)
}
