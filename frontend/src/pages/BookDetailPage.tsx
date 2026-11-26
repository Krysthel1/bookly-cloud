import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Heart, Minus, Plus, ShoppingBag, Star } from 'lucide-react'
import { toast } from 'sonner'
import { catalogApi, favoritesApi } from '@/services/booklyApi'
import { useAuthStore } from '@/stores/useAuthStore'
import { useCartStore } from '@/stores/useCartStore'
import { formatDatePE, formatPEN } from '@/lib/utils'
import { extractApiError } from '@/lib/api'
import { BookCard } from '@/components/books/BookCard'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input, Textarea } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/card'

export function BookDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const session = useAuthStore((s) => s.session)
  const addBook = useCartStore((s) => s.addBook)

  const [quantity, setQuantity] = useState(1)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [rating, setRating] = useState(5)
  const [reviewTitle, setReviewTitle] = useState('')
  const [reviewComment, setReviewComment] = useState('')

  const { data: book, isLoading } = useQuery({
    queryKey: ['book-detail', id],
    queryFn: () => catalogApi.getBook(id!),
    enabled: Boolean(id),
  })

  const { data: related } = useQuery({
    queryKey: ['book-related', id],
    queryFn: () => catalogApi.getRelated(id!),
    enabled: Boolean(id),
  })

  const { data: reviews } = useQuery({
    queryKey: ['book-reviews', id],
    queryFn: () => catalogApi.getReviews(id!),
    enabled: Boolean(id),
  })

  const reviewMutation = useMutation({
    mutationFn: () =>
      catalogApi.createReview(id!, {
        rating,
        title: reviewTitle || undefined,
        comment: reviewComment,
      }),
    onSuccess: () => {
      toast.success('Reseña publicada correctamente')
      setReviewTitle('')
      setReviewComment('')
      queryClient.invalidateQueries({ queryKey: ['book-reviews', id] })
      queryClient.invalidateQueries({ queryKey: ['book-detail', id] })
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  if (isLoading) {
    return (
      <div className="container py-12 grid gap-10 md:grid-cols-12">
        <Skeleton className="aspect-[3/4] md:col-span-5" />
        <div className="space-y-4 md:col-span-7">
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-5 w-1/3" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    )
  }

  if (!book) {
    return (
      <div className="container py-20 text-center">
        <h1 className="font-serif text-3xl font-bold">Libro no encontrado</h1>
        <Button className="mt-4" asChild>
          <Link to="/catalogo">Volver al catálogo</Link>
        </Button>
      </div>
    )
  }

  const gallery =
    book.images.length > 0
      ? book.images.map((i) => i.image_url)
      : book.cover_url
        ? [book.cover_url]
        : []
  const activeImage = selectedImage || gallery[0] || null
  const outOfStock = book.stock <= 0

  const handleBuyNow = async () => {
    await addBook(book, quantity)
    navigate('/checkout')
  }

  return (
    <div className="container py-10 space-y-16">
      <nav className="text-xs text-muted-foreground">
        <Link to="/" className="hover:text-primary">Inicio</Link> /{' '}
        <Link to="/catalogo" className="hover:text-primary">Catálogo</Link> /{' '}
        <span className="text-foreground">{book.title}</span>
      </nav>

      <div className="grid gap-10 lg:grid-cols-12">
        {/* Galería */}
        <div className="space-y-4 lg:col-span-5">
          <div className="aspect-[3/4] overflow-hidden rounded-2xl border bg-card">
            {activeImage ? (
              <img
                src={activeImage}
                alt={book.title}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full items-center justify-center bg-bookly-forest p-8 text-center text-bookly-cream">
                <p className="font-serif text-2xl font-bold">{book.title}</p>
              </div>
            )}
          </div>
          {gallery.length > 1 && (
            <div className="flex gap-3 overflow-x-auto">
              {gallery.map((imgUrl, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedImage(imgUrl)}
                  className={`h-20 w-16 overflow-hidden rounded-lg border-2 ${
                    activeImage === imgUrl ? 'border-primary' : 'border-transparent'
                  }`}
                >
                  <img src={imgUrl} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detalles */}
        <div className="space-y-6 lg:col-span-7">
          <div className="flex flex-wrap gap-2">
            {book.categories.map((c) => (
              <Badge key={c.id} variant="secondary">
                {c.name}
              </Badge>
            ))}
            {Number(book.discount_percent) > 0 && (
              <Badge variant="gold">-{Number(book.discount_percent).toFixed(0)}% de descuento</Badge>
            )}
          </div>

          <div>
            <h1 className="font-serif text-3xl font-bold sm:text-4xl">{book.title}</h1>
            <p className="mt-2 text-base text-muted-foreground">
              Por{' '}
              <span className="font-medium text-foreground">
                {book.authors.map((a) => a.name).join(', ')}
              </span>
            </p>
            <div className="mt-3 flex items-center gap-4 text-sm">
              <span className="inline-flex items-center gap-1 font-medium text-bookly-gold">
                <Star className="h-4 w-4 fill-bookly-gold" />
                {Number(book.average_rating).toFixed(1)}
              </span>
              <span className="text-muted-foreground">({book.reviews_count} reseñas)</span>
              <span className="text-muted-foreground">•</span>
              <span className={outOfStock ? 'text-destructive font-medium' : 'text-emerald-700 dark:text-emerald-400 font-medium'}>
                {outOfStock ? 'Agotado' : `${book.stock} disponibles`}
              </span>
            </div>
          </div>

          <div className="rounded-xl border bg-card/50 p-5">
            <div className="flex items-baseline gap-3">
              <span className="font-serif text-3xl font-bold text-primary">
                {formatPEN(book.final_price)}
              </span>
              {Number(book.discount_percent) > 0 && (
                <span className="text-base text-muted-foreground line-through">
                  {formatPEN(book.price)}
                </span>
              )}
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <div className="flex items-center rounded-md border bg-background">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  disabled={quantity <= 1}
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  aria-label="Disminuir cantidad"
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-10 text-center text-sm font-semibold">{quantity}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  disabled={quantity >= book.stock}
                  onClick={() => setQuantity((q) => Math.min(book.stock, q + 1))}
                  aria-label="Aumentar cantidad"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>

              <Button
                size="lg"
                disabled={outOfStock}
                onClick={() => addBook(book, quantity)}
              >
                <ShoppingBag className="h-4 w-4" />
                Agregar al carrito
              </Button>

              <Button
                size="lg"
                variant="gold"
                disabled={outOfStock}
                onClick={handleBuyNow}
              >
                Comprar ahora
              </Button>

              <Button
                size="icon"
                variant="outline"
                aria-label="Guardar en favoritos"
                onClick={() => {
                  if (!session) {
                    toast.info('Inicia sesión para guardar favoritos')
                    return
                  }
                  favoritesApi.add(book.id).then(() => {
                    queryClient.invalidateQueries({ queryKey: ['favorites'] })
                    toast.success('Agregado a favoritos')
                  })
                }}
              >
                <Heart className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="font-serif text-xl font-semibold">Sinopsis</h2>
            <p className="text-sm leading-relaxed text-muted-foreground">{book.synopsis}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 rounded-xl border p-4 text-sm sm:grid-cols-3">
            <div>
              <p className="text-xs text-muted-foreground">Editorial</p>
              <p className="font-medium">{book.publisher?.name || 'Independiente'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">ISBN</p>
              <p className="font-medium">{book.isbn}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Páginas</p>
              <p className="font-medium">{book.pages || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Idioma</p>
              <p className="font-medium">{book.language}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Publicación</p>
              <p className="font-medium">{formatDatePE(book.publication_date)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Reseñas */}
      <section className="space-y-6 border-t pt-12">
        <h2 className="font-serif text-2xl font-bold">Reseñas de lectores</h2>
        <div className="grid gap-8 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-7">
            {!reviews || reviews.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Aún no hay reseñas para este libro. ¡Sé el primero en opinar!
              </p>
            ) : (
              reviews.map((rev) => (
                <div key={rev.id} className="rounded-xl border bg-card/40 p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-sm">{rev.user_name}</p>
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-bookly-gold">
                      <Star className="h-3.5 w-3.5 fill-bookly-gold" />
                      {rev.rating}/5
                    </span>
                  </div>
                  {rev.title && <p className="font-serif font-semibold">{rev.title}</p>}
                  <p className="text-sm text-muted-foreground">{rev.comment}</p>
                  <p className="text-xs text-muted-foreground">{formatDatePE(rev.created_at)}</p>
                </div>
              ))
            )}
          </div>

          <div className="lg:col-span-5">
            <div className="rounded-xl border bg-card/50 p-6 space-y-4">
              <h3 className="font-serif text-lg font-semibold">Escribir una reseña</h3>
              {!session ? (
                <div className="space-y-3 text-sm text-muted-foreground">
                  <p>Inicia sesión para compartir tu opinión sobre este libro.</p>
                  <Button asChild size="sm">
                    <Link to="/iniciar-sesion">Iniciar sesión</Link>
                  </Button>
                </div>
              ) : (
                <form
                  onSubmit={(e) => {
                    e.preventDefault()
                    reviewMutation.mutate()
                  }}
                  className="space-y-3"
                >
                  <div>
                    <label className="text-xs font-medium">Calificación</label>
                    <select
                      value={rating}
                      onChange={(e) => setRating(Number(e.target.value))}
                      className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    >
                      {[5, 4, 3, 2, 1].map((n) => (
                        <option key={n} value={n}>
                          {n} estrellas
                        </option>
                      ))}
                    </select>
                  </div>
                  <Input
                    value={reviewTitle}
                    onChange={(e) => setReviewTitle(e.target.value)}
                    placeholder="Título breve (opcional)"
                  />
                  <Textarea
                    required
                    minLength={5}
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    placeholder="¿Qué te pareció la edición y la lectura?"
                  />
                  <Button type="submit" disabled={reviewMutation.isPending}>
                    {reviewMutation.isPending ? 'Publicando...' : 'Publicar reseña'}
                  </Button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Libros relacionados */}
      {related && related.length > 0 && (
        <section className="space-y-6 border-t pt-12">
          <h2 className="font-serif text-2xl font-bold">Libros relacionados</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {related.map((item) => (
              <BookCard key={item.id} book={item} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
