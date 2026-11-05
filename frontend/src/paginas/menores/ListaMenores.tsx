import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { listarMenores } from '../../api/menores'
import { obtenerYo } from '../../api/usuarios'
import {
  claseBotonPrincipal,
  claseBotonSecundario,
  claseCampo,
  normalizar,
} from '../miembros/utilidades'
import { CATEGORIAS, esGestor, useCarga } from './utilidades'

export default function ListaMenores() {
  const [busqueda, setBusqueda] = useState('')
  const ubicacion = useLocation()
  const { estado, reintentar } = useCarga(async () => {
    const yo = await obtenerYo()
    return esGestor(yo.cargo) ? await listarMenores() : null
  })
  if (estado.tipo === 'cargando') return <p role="status">Cargando niños y adolescentes…</p>
  if (estado.tipo === 'error')
    return (
      <div role="alert">
        <p>{estado.mensaje}</p>
        <button className={claseBotonSecundario} onClick={reintentar}>
          Reintentar
        </button>
      </div>
    )
  if (estado.datos === null)
    return (
      <div role="alert">
        <h1 className="text-2xl font-bold">Sin acceso</h1>
        <p>Solo el pastor, su apoyo y el presbítero pueden gestionar estos registros.</p>
      </div>
    )
  const menores = estado.datos.filter((m) => normalizar(m.nombre).includes(normalizar(busqueda)))
  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Niños y adolescentes</h1>
          <p className="mt-2 text-texto-suave">Registros de 4 a 17 años, con sus tutores.</p>
        </div>
        <Link className={claseBotonPrincipal} to="/menores/nuevo">
          Registrar menor
        </Link>
      </div>
      {ubicacion.state?.guardado && (
        <p role="status" className="rounded-xl bg-acento p-3 text-acento-texto">
          Registro guardado.
        </p>
      )}
      <label className="block text-sm font-semibold">
        Buscar por nombre
        <input
          type="search"
          className={claseCampo}
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
      </label>
      {menores.length === 0 ? (
        <p className="rounded-2xl border border-borde bg-superficie p-6">
          {busqueda ? 'No hay coincidencias.' : 'Todavía no hay menores registrados en tu alcance.'}
        </p>
      ) : (
        <ul className="grid gap-4 lg:grid-cols-2">
          {menores.map((m) => (
            <li key={m.id} className="rounded-2xl border border-borde bg-superficie p-5">
              <div className="flex flex-wrap justify-between gap-3">
                <h2 className="text-lg font-semibold break-words">{m.nombre}</h2>
                <span className="text-sm text-texto-suave">{m.activo ? 'Activo' : 'Inactivo'}</span>
              </div>
              <p className="mt-1">
                {m.categoria ? CATEGORIAS[m.categoria] : 'Fuera del rango de edad'} · {m.edad} años
              </p>
              <p className="mt-1 text-sm text-texto-suave">{m.iglesia_nombre}</p>
              <Link
                className={claseBotonSecundario + ' mt-4'}
                to={`/menores/${m.id}/editar`}
                aria-label={`Ver y editar el registro de ${m.nombre}`}
              >
                Ver y editar
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
