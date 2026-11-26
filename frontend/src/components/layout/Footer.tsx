import { Link } from 'react-router-dom'
import { BookMarked } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t bg-bookly-forest text-bookly-cream">
      <div className="container grid gap-10 py-14 md:grid-cols-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-bookly-gold text-bookly-charcoal">
              <BookMarked className="h-4 w-4" />
            </div>
            <span className="font-serif text-lg font-bold tracking-wider">BOOKLY</span>
          </div>
          <p className="text-sm text-bookly-sage leading-relaxed">
            Librería digital curada en Perú. Ediciones seleccionadas de literatura, pensamiento e
            ingeniería con envío protegido.
          </p>
        </div>

        <div>
          <h4 className="mb-3 font-serif text-sm font-semibold uppercase tracking-wider text-bookly-gold">
            Explorar
          </h4>
          <ul className="space-y-2 text-sm text-bookly-cream/85">
            <li><Link to="/catalogo" className="hover:text-bookly-gold">Catálogo completo</Link></li>
            <li><Link to="/catalogo?sort=best_sellers" className="hover:text-bookly-gold">Más vendidos</Link></li>
            <li><Link to="/catalogo?sort=newest" className="hover:text-bookly-gold">Nuevos lanzamientos</Link></li>
            <li><Link to="/catalogo?on_sale=true" className="hover:text-bookly-gold">Ofertas especiales</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="mb-3 font-serif text-sm font-semibold uppercase tracking-wider text-bookly-gold">
            Librería
          </h4>
          <ul className="space-y-2 text-sm text-bookly-cream/85">
            <li><Link to="/nosotros" className="hover:text-bookly-gold">Sobre nosotros</Link></li>
            <li><Link to="/preguntas-frecuentes" className="hover:text-bookly-gold">Preguntas frecuentes</Link></li>
            <li><Link to="/contacto" className="hover:text-bookly-gold">Contacto</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="mb-3 font-serif text-sm font-semibold uppercase tracking-wider text-bookly-gold">
            Legal
          </h4>
          <ul className="space-y-2 text-sm text-bookly-cream/85">
            <li><Link to="/privacidad" className="hover:text-bookly-gold">Políticas de privacidad</Link></li>
            <li><Link to="/terminos" className="hover:text-bookly-gold">Términos y condiciones</Link></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/10 py-5">
        <div className="container flex flex-col items-center justify-between gap-3 text-xs text-bookly-sage sm:flex-row">
          <p>© {new Date().getFullYear()} BOOKLY Librería Digital. Todos los derechos reservados.</p>
          <p>Precios expresados en soles peruanos (S/). Pagos simulados con fines académicos.</p>
        </div>
      </div>
    </footer>
  )
}
