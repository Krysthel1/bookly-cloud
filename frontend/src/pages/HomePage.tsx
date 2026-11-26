import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Award, BookOpen, ShieldCheck, Sparkles, Truck } from 'lucide-react'
import { toast } from 'sonner'
import { catalogApi, favoritesApi } from '@/services/booklyApi'
import { useAuthStore } from '@/stores/useAuthStore'
import { BookCard, BookCardSkeleton } from '@/components/books/BookCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

export function HomePage() {
  const [newsletterEmail, setNewsletterEmail] = useState('')
  const session = useAuthStore((s) => s.session)
  const queryClient = useQueryClient()

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: () => catalogApi.getCategories(),
  })

  const { data: featured, isLoading: loadingFeatured } = useQuery({
    queryKey: ['books', 'featured'],
    queryFn: () => catalogApi.getFeatured(4),
  })

  const { data: bestSellers, isLoading: loadingBest } = useQuery({
    queryKey: ['books', 'best-sellers'],
    queryFn: () => catalogApi.getBestSellers(4),
  })

  const { data: newReleases, isLoading: loadingNew } = useQuery({
    queryKey: ['books', 'new-releases'],
    queryFn: () => catalogApi.getNewReleases(4),
  })

  const { data: offers } = useQuery({
    queryKey: ['books', 'offers'],
    queryFn: () => catalogApi.getBooks({ on_sale: true, page_size: 4 }),
  })

  const { data: authorsData } = useQuery({
    queryKey: ['authors', 'featured'],
    queryFn: () => catalogApi.getAuthors({ featured: true, page_size: 6 }),
  })

  const { data: favorites } = useQuery({
    queryKey: ['favorites'],
    queryFn: () => favoritesApi.list(),
    enabled: Boolean(session),
  })

  const favIds = new Set((favorites || []).map((b) => b.id))

  const favMutation = useMutation({
    mutationFn: async (bookId: string) => {
      if (favIds.has(bookId)) return favoritesApi.remove(bookId)
      return favoritesApi.add(bookId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
      toast.success('Lista de favoritos actualizada')
    },
  })

  const handleToggleFavorite = (bookId: string) => {
    if (!session) {
      toast.info('Inicia sesión para guardar tus libros favoritos')
      return
    }
    favMutation.mutate(bookId)
  }

  const handleNewsletter = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newsletterEmail.trim()) return
    toast.success('¡Gracias por suscribirte al boletín editorial de BOOKLY!')
    setNewsletterEmail('')
  }

  return (
    <div className="space-y-20 pb-20">
      {/* Hero editorial */}
      <section className="relative overflow-hidden border-b bg-bookly-cream dark:bg-card/40">
        <div className="container grid items-center gap-12 py-16 md:grid-cols-12 md:py-24">
          <div className="space-y-6 md:col-span-7 animate-fade-in-up">
            <Badge variant="gold" className="px-3 py-1">
              Librería Digital Curada • Perú
            </Badge>
            <h1 className="font-serif text-4xl font-bold leading-tight text-bookly-forest dark:text-bookly-cream sm:text-5xl lg:text-6xl">
              Historias que permanecen, ediciones pensadas para durar.
            </h1>
            <p className="max-w-xl text-base text-muted-foreground sm:text-lg leading-relaxed">
              Explora literatura latinoamericana, clásicos universales, pensamiento contemporáneo y
              obras técnicas seleccionadas. Compra segura con despacho a todo el Perú.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button size="lg" asChild>
                <Link to="/catalogo">
                  Explorar catálogo
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link to="/catalogo?on_sale=true">Ver ofertas especiales</Link>
              </Button>
            </div>
          </div>

          <div className="md:col-span-5">
            <div className="relative rounded-2xl border bg-bookly-forest p-8 text-bookly-cream shadow-sm">
              <p className="text-xs uppercase tracking-[0.22em] text-bookly-gold">
                Selección del Mes
              </p>
              <h2 className="mt-3 font-serif text-2xl font-semibold">
                Clásicos Peruanos &amp; Arquitectura de Software
              </h2>
              <p className="mt-3 text-sm text-bookly-sage leading-relaxed">
                Usa el cupón <strong className="text-bookly-gold">BOOKLY10</strong> para obtener 10%
                de descuento adicional en pedidos desde S/ 50.00. Envío estándar gratuito desde S/
                120.00.
              </p>
              <div className="mt-6 grid grid-cols-3 gap-3 border-t border-white/15 pt-5 text-center">
                <div>
                  <p className="font-serif text-2xl font-bold text-bookly-gold">40+</p>
                  <p className="text-xs text-bookly-sage">Títulos curados</p>
                </div>
                <div>
                  <p className="font-serif text-2xl font-bold text-bookly-gold">24h</p>
                  <p className="text-xs text-bookly-sage">Despacho Lima</p>
                </div>
                <div>
                  <p className="font-serif text-2xl font-bold text-bookly-gold">S/</p>
                  <p className="text-xs text-bookly-sage">Pago local</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categorías populares */}
      <section className="container space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
              Colecciones
            </p>
            <h2 className="font-serif text-3xl font-bold">Categorías populares</h2>
          </div>
          <Link to="/catalogo" className="text-sm font-medium text-primary hover:underline">
            Ver todas →
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {(categoriesData?.items || []).slice(0, 8).map((cat) => (
            <Link
              key={cat.id}
              to={`/catalogo?category=${cat.slug}`}
              className="group rounded-xl border bg-card/50 p-5 transition hover:border-primary/40 hover:bg-card"
            >
              <div className="flex items-center justify-between">
                <BookOpen className="h-5 w-5 text-primary" />
                <span className="text-xs text-muted-foreground">{cat.books_count} títulos</span>
              </div>
              <h3 className="mt-3 font-serif text-lg font-semibold group-hover:text-primary">
                {cat.name}
              </h3>
              <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{cat.description}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Libros destacados */}
      <section className="container space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
              Curaduría
            </p>
            <h2 className="font-serif text-3xl font-bold">Libros destacados</h2>
          </div>
          <Link to="/catalogo" className="text-sm font-medium text-primary hover:underline">
            Ver catálogo →
          </Link>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {loadingFeatured
            ? Array.from({ length: 4 }).map((_, i) => <BookCardSkeleton key={i} />)
            : (featured || []).map((book) => (
                <BookCard
                  key={book.id}
                  book={book}
                  isFavorite={favIds.has(book.id)}
                  onToggleFavorite={handleToggleFavorite}
                />
              ))}
        </div>
      </section>

      {/* Más vendidos */}
      <section className="container space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
              Top Lectores
            </p>
            <h2 className="font-serif text-3xl font-bold">Los más vendidos</h2>
          </div>
          <Link
            to="/catalogo?sort=best_sellers"
            className="text-sm font-medium text-primary hover:underline"
          >
            Ver ranking →
          </Link>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {loadingBest
            ? Array.from({ length: 4 }).map((_, i) => <BookCardSkeleton key={i} />)
            : (bestSellers || []).map((book) => (
                <BookCard
                  key={book.id}
                  book={book}
                  isFavorite={favIds.has(book.id)}
                  onToggleFavorite={handleToggleFavorite}
                />
              ))}
        </div>
      </section>

      {/* Nuevos lanzamientos & Ofertas */}
      <section className="bg-card/50 py-16 border-y">
        <div className="container space-y-14">
          <div className="space-y-6">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
                  Novedades
                </p>
                <h2 className="font-serif text-3xl font-bold">Nuevos lanzamientos</h2>
              </div>
              <Link
                to="/catalogo?sort=newest"
                className="text-sm font-medium text-primary hover:underline"
              >
                Explorar novedades →
              </Link>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {loadingNew
                ? Array.from({ length: 4 }).map((_, i) => <BookCardSkeleton key={i} />)
                : (newReleases || []).map((book) => (
                    <BookCard
                      key={book.id}
                      book={book}
                      isFavorite={favIds.has(book.id)}
                      onToggleFavorite={handleToggleFavorite}
                    />
                  ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
                  Promociones
                </p>
                <h2 className="font-serif text-3xl font-bold">Ofertas especiales</h2>
              </div>
              <Link
                to="/catalogo?on_sale=true"
                className="text-sm font-medium text-primary hover:underline"
              >
                Ver todas las ofertas →
              </Link>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {(offers?.items || []).map((book) => (
                <BookCard
                  key={book.id}
                  book={book}
                  isFavorite={favIds.has(book.id)}
                  onToggleFavorite={handleToggleFavorite}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Autores destacados */}
      <section className="container space-y-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
            Voces Imprescindibles
          </p>
          <h2 className="font-serif text-3xl font-bold">Autores destacados</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(authorsData?.items || []).map((author) => (
            <Link
              key={author.id}
              to={`/catalogo?author_id=${author.id}`}
              className="flex flex-col justify-between rounded-xl border bg-background p-5 transition hover:border-primary/40"
            >
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-serif text-lg font-semibold">{author.name}</h3>
                  <Badge variant="outline">{author.nationality || 'Internacional'}</Badge>
                </div>
                <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                  {author.biography}
                </p>
              </div>
              <p className="mt-4 text-xs font-medium text-primary">
                {author.books_count} libros disponibles →
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* Beneficios */}
      <section className="container">
        <div className="grid gap-6 rounded-2xl border bg-card/60 p-8 md:grid-cols-4">
          <div className="space-y-2">
            <Truck className="h-6 w-6 text-primary" />
            <h3 className="font-serif text-lg font-semibold">Envío a todo el Perú</h3>
            <p className="text-sm text-muted-foreground">
              Envío estándar gratis en compras desde S/ 120.00 y seguimiento en tiempo real.
            </p>
          </div>
          <div className="space-y-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            <h3 className="font-serif text-lg font-semibold">Compra protegida</h3>
            <p className="text-sm text-muted-foreground">
              Stock verificado en tiempo real y autenticación segura respaldada por Supabase.
            </p>
          </div>
          <div className="space-y-2">
            <Award className="h-6 w-6 text-primary" />
            <h3 className="font-serif text-lg font-semibold">Ediciones originales</h3>
            <p className="text-sm text-muted-foreground">
              Trabajamos directamente con editoriales reconocidas de Perú, España y Latinoamérica.
            </p>
          </div>
          <div className="space-y-2">
            <Sparkles className="h-6 w-6 text-primary" />
            <h3 className="font-serif text-lg font-semibold">Cupones y beneficios</h3>
            <p className="text-sm text-muted-foreground">
              Descuentos exclusivos para lectores registrados y lanzamientos anticipados.
            </p>
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="container">
        <div className="rounded-2xl bg-bookly-forest p-8 text-bookly-cream md:flex md:items-center md:justify-between md:p-12">
          <div className="max-w-lg space-y-2">
            <h2 className="font-serif text-2xl font-bold sm:text-3xl">
              Recibe reseñas y lanzamientos en tu correo
            </h2>
            <p className="text-sm text-bookly-sage">
              Cada semana compartimos recomendaciones literarias y cupones especiales para nuestra
              comunidad de lectores.
            </p>
          </div>
          <form onSubmit={handleNewsletter} className="mt-6 flex w-full max-w-md gap-2 md:mt-0">
            <Input
              type="email"
              required
              value={newsletterEmail}
              onChange={(e) => setNewsletterEmail(e.target.value)}
              placeholder="tu@correo.com"
              className="bg-background text-foreground"
            />
            <Button type="submit" variant="gold">
              Suscribirme
            </Button>
          </form>
        </div>
      </section>
    </div>
  )
}
