import { useEffect, useState } from 'react'
import { obtenerToken } from '../api/cliente'
import { obtenerYo, type Cargo } from '../api/usuarios'
import type { EntradaMenu } from './tipos'

// El cargo se pide una sola vez por sesión (el menú y el Inicio lo usan a la vez).
let guardado: { token: string; cargo: Promise<Cargo | null> } | null = null

function cargoDeLaSesion(): Promise<Cargo | null> {
  const token = obtenerToken() ?? ''
  if (!guardado || guardado.token !== token) {
    guardado = {
      token,
      cargo: obtenerYo().then(
        (yo) => yo.cargo,
        () => null,
      ),
    }
  }
  return guardado.cargo
}

/**
 * Deja solo las entradas del menú que el cargo de la persona puede usar.
 * Mientras llega el cargo (o si no se pudo saber) solo se muestran las entradas sin restricción.
 */
export function useMenuVisible(menu: EntradaMenu[]): EntradaMenu[] {
  const [sesion, setSesion] = useState<{ token: string; cargo: Cargo | null }>({
    token: '',
    cargo: null,
  })
  const token = obtenerToken() ?? ''

  useEffect(() => {
    let vigente = true
    cargoDeLaSesion().then((cargo) => vigente && setSesion({ token, cargo }))
    return () => {
      vigente = false
    }
  }, [token])

  const cargo = sesion.token === token ? sesion.cargo : null
  return menu.filter((e) => !e.cargos || (cargo !== null && e.cargos.includes(cargo)))
}
