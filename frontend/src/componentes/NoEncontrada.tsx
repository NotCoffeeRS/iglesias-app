import { Link } from 'react-router-dom'

export default function NoEncontrada() {
  return (
    <section className="py-12 text-center">
      <p className="font-titulo text-7xl font-bold text-acento">404</p>
      <h1 className="mt-2 text-2xl font-bold">Esta página no existe</h1>
      <p className="mt-2 text-texto-suave">Revisa la dirección o vuelve al inicio.</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-xl bg-primario px-5 py-2.5 font-semibold text-sobre-primario hover:bg-primario-hover"
      >
        Volver al inicio
      </Link>
    </section>
  )
}
