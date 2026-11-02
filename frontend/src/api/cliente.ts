// Cliente HTTP para la API de FastAPI. Todas las pantallas deben pasar por aquí.

/** URL base de la API, tomada de la variable de entorno VITE_API_URL (sin "/" al final). */
export const URL_API: string = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/+$/,
  '',
)

const CLAVE_TOKEN = 'iglesias.token'

/** Se emite en `window` cuando la API rechaza el token (vencido o alterado) y se borra la sesión. */
export const EVENTO_SESION_EXPIRADA = 'iglesias:sesion-expirada'

export function obtenerToken(): string | null {
  try {
    return localStorage.getItem(CLAVE_TOKEN)
  } catch {
    return null
  }
}

export function guardarToken(token: string): void {
  try {
    localStorage.setItem(CLAVE_TOKEN, token)
  } catch {
    // Sin almacenamiento (modo privado bloqueado): la sesión no se conserva.
  }
}

export function borrarToken(): void {
  try {
    localStorage.removeItem(CLAVE_TOKEN)
  } catch {
    // Nada que borrar.
  }
}

/** Error de una respuesta no exitosa. `estado` es el código HTTP (0 si no hubo conexión). */
export class ErrorApi extends Error {
  estado: number
  detalle: unknown

  constructor(estado: number, mensaje: string, detalle?: unknown) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
    this.detalle = detalle
  }
}

type Metodo = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

/** Convierte el `detail` de FastAPI (texto o lista de validaciones) en un mensaje legible. */
function mensajeDeError(estado: number, cuerpo: unknown): string {
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    const textos = detalle
      .map((d) => (d as { msg?: unknown })?.msg)
      .filter((m): m is string => typeof m === 'string')
    if (textos.length) return textos.join('. ')
  }
  return `Error ${estado} al comunicarse con el servidor`
}

async function peticion<T>(metodo: Metodo, ruta: string, cuerpo?: unknown): Promise<T> {
  const encabezados: Record<string, string> = { Accept: 'application/json' }
  const token = obtenerToken()
  if (token) encabezados.Authorization = `Bearer ${token}`
  if (cuerpo !== undefined) encabezados['Content-Type'] = 'application/json'

  let respuesta: Response
  try {
    respuesta = await fetch(`${URL_API}${ruta.startsWith('/') ? ruta : `/${ruta}`}`, {
      method: metodo,
      headers: encabezados,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch (error) {
    throw new ErrorApi(0, 'No se pudo conectar con el servidor', error)
  }

  const texto = await respuesta.text()
  let datos: unknown = null
  if (texto) {
    try {
      datos = JSON.parse(texto)
    } catch {
      datos = texto
    }
  }

  if (!respuesta.ok) {
    if (respuesta.status === 401 && token) {
      borrarToken()
      window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA))
    }
    throw new ErrorApi(respuesta.status, mensajeDeError(respuesta.status, datos), datos)
  }
  return datos as T
}

/** Uso: `const miembros = await api.get<Miembro[]>('/miembros')`. */
export const api = {
  get: <T>(ruta: string) => peticion<T>('GET', ruta),
  post: <T>(ruta: string, cuerpo?: unknown) => peticion<T>('POST', ruta, cuerpo),
  put: <T>(ruta: string, cuerpo?: unknown) => peticion<T>('PUT', ruta, cuerpo),
  patch: <T>(ruta: string, cuerpo?: unknown) => peticion<T>('PATCH', ruta, cuerpo),
  delete: <T>(ruta: string) => peticion<T>('DELETE', ruta),
}
