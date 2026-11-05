import { useMemo, useState } from 'react'
import Icono from '../../componentes/Icono'
import { Link, useLocation } from 'react-router-dom'
import { listarUsuarios, obtenerYo, type UsuarioResumen } from '../../api/usuarios'
import { Cargando, ErrorConReintento, SinPermiso } from './comunes'
import { puedeEditarA, puedeGestionar } from './reglas'
import { claseBotonPrincipal, claseCampo, nombreCargo, normalizar, useCarga } from './utilidades'

async function cargarTodo() {
  const yo = await obtenerYo()
  // Quien no administra cuentas no pide la lista: el servidor la rechazaría con 403.
  const usuarios = puedeGestionar(yo) ? await listarUsuarios() : []
  return { yo, usuarios }
}

function Fila({ u, editable }: { u: UsuarioResumen; editable: boolean }) {
  const contenido = (
    <>
      <span className="block truncate font-semibold">{u.nombre_completo}</span>
      <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-texto-suave">
        <span className="rounded-full bg-acento px-2.5 py-0.5 text-xs font-semibold text-acento-texto">
          {nombreCargo(u.cargo)}
        </span>
        {!u.activo && (
          <span className="rounded-full border border-borde px-2.5 py-0.5 text-xs font-semibold">
            Inactivo
          </span>
        )}
        <span className="min-w-0 truncate">{u.nombre_usuario}</span>
        {u.iglesia_nombre && <span className="min-w-0 truncate">· {u.iglesia_nombre}</span>}
      </span>
    </>
  )
  return editable ? (
    <Link
      to={`/usuarios/${u.id}/editar`}
      className="block px-4 py-3.5 transition-colors hover:bg-superficie-2"
    >
      {contenido}
    </Link>
  ) : (
    <div className="px-4 py-3.5">{contenido}</div>
  )
}

export default function ListaUsuarios() {
  const aviso = (useLocation().state as { aviso?: string } | null)?.aviso
  const [busqueda, setBusqueda] = useState('')
  const { estado, reintentar } = useCarga(cargarTodo, 'cargar los usuarios')

  const visibles = useMemo(() => {
    if (estado.tipo !== 'listo') return []
    const texto = normalizar(busqueda)
    const lista = texto
      ? estado.datos.usuarios.filter((u) =>
          normalizar(`${u.nombre_completo} ${u.nombre_usuario}`).includes(texto),
        )
      : estado.datos.usuarios
    // Los activos primero; dentro de cada grupo, por nombre.
    return [...lista].sort(
      (a, b) =>
        Number(b.activo) - Number(a.activo) ||
        a.nombre_completo.localeCompare(b.nombre_completo, 'es'),
    )
  }, [estado, busqueda])

  const yo = estado.tipo === 'listo' ? estado.datos.yo : null
  const gestiona = yo ? puedeGestionar(yo) : false
  const variasIglesias =
    estado.tipo === 'listo' && new Set(estado.datos.usuarios.map((u) => u.iglesia_id)).size > 1

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold md:text-4xl">Usuarios</h1>
          <p className="mt-1 text-texto-suave">Cuentas del liderazgo y el cargo de cada una.</p>
        </div>
        {gestiona && (
          <Link to="/usuarios/nuevo" className={claseBotonPrincipal}>
            Crear usuario
          </Link>
        )}
      </div>

      {aviso && (
        <p
          role="status"
          className="mt-4 rounded-xl bg-acento px-4 py-2.5 font-semibold text-acento-texto"
        >
          {aviso}
        </p>
      )}

      <div className="mt-5">
        {estado.tipo === 'cargando' && <Cargando />}
        {estado.tipo === 'error' && (
          <ErrorConReintento mensaje={estado.mensaje} reintentar={reintentar} />
        )}
        {yo && !gestiona && <SinPermiso />}
        {yo && gestiona && (
          <>
            <label className="block max-w-md text-sm font-semibold">
              Buscar por nombre o usuario
              <span className="relative mt-1.5 block">
                <Icono
                  nombre="buscar"
                  className="pointer-events-none absolute top-1/2 left-3.5 h-5 w-5 -translate-y-1/2 text-texto-suave"
                />
                <input
                  type="search"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  autoComplete="off"
                  className={claseCampo + ' mt-0! pl-11'}
                />
              </span>
            </label>
            <div className="mt-4">
              {visibles.length === 0 ? (
                <p className="rounded-3xl border border-borde bg-superficie p-6 text-texto-suave">
                  {busqueda
                    ? `Nadie coincide con “${busqueda.trim()}”.`
                    : 'Todavía no hay usuarios. Crea el primero.'}
                </p>
              ) : (
                <ul className="divide-y divide-borde overflow-hidden rounded-3xl border border-borde bg-superficie">
                  {visibles.map((u) => (
                    <li key={u.id}>
                      <Fila
                        u={variasIglesias ? u : { ...u, iglesia_nombre: null }}
                        editable={puedeEditarA(yo, u)}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </section>
  )
}
