import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, ShoppingBag, Star } from 'lucide-react'
import type { Book } from '@/types'
import { formatPEN } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/card'
import { useCartStore } from '@/stores/useCartStore'

interface BookCardProps {
  book: Book
  isFavorite?: boolean
  onToggleFavorite?: (bookId: string) => void
}

export function BookCard({ book, isFavorite = false, onToggleFavorite }: BookCardProps) {
  const addBook = useCartStore((s) => s.addBook)
  const [imgError, setImgError] = useState(false)

  const discount = Number(book.discount_percent || 0)
  const hasDiscount = discount > 0
  const outOfStock = book.stock <= 0
  const authorNames = book.authors.map((a) => a.name).join(', ') || 'Autor BOOKLY'

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-xl border bg-background transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md">
      <Link
        to={`/libros/${book.slug}`}
        className="relative aspect-[3/4] w-full overflow-hidden bg-card"
      >
        {book.cover_url && !imgError ? (
          <img
            src={book.cover_url}
            alt={`Portada de ${book.title}`}
            loading="lazy"
            onError={() => setImgError(true)}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full flex-col justify-between bg-bookly-forest p-5 text-bookly-cream">
            <span className="text-[10px] uppercase tracking-[0.2em] text-bookly-gold">
              Edición BOOKLY
            </span>
            <div>
              <p className="font-serif text-lg font-semibold leading-snug line-clamp-4">
                {book.title}
              </p>
              <p className="mt-2 text-xs text-bookly-sage line-clamp-1">{authorNames}</p>
            </div>
            <span className="text-[11px] opacity-70">ISBN {book.isbn}</span>
          </div>
        )}

        <div className="absolute left-3 top-3 flex flex-col gap-1.5">
          {hasDiscount && (
            <Badge variant="gold" className="bg-bookly-gold text-bookly-charcoal font-semibold">
              -{discount.toFixed(0)}%
            </Badge>
          )}
          {outOfStock && <Badge variant="destructive">Agotado</Badge>}
        </div>

        {onToggleFavorite && (
          <button
            type="button"
            aria-label={isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}
            onClick={(e) => {
              e.preventDefault()
              onToggleFavorite(book.id)
            }}
            className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-background/90 text-foreground shadow-sm backdrop-blur-sm transition hover:scale-105"
          >
            <Heart
              className={`h-4 w-4 ${isFavorite ? 'fill-rose-500 text-rose-500' : 'text-muted-foreground'}`}
            />
          </button>
        )}
      </Link>

      <div className="flex flex-1 flex-col justify-between p-4">
        <div>
          <div className="mb-1 flex items-center justify-between gap-2 text-xs text-muted-foreground">
            <span className="truncate">{book.categories[0]?.name || 'Editorial'}</span>
            <span className="inline-flex items-center gap-1 text-bookly-gold">
              <Star className="h-3.5 w-3.5 fill-bookly-gold" />
              {Number(book.average_rating).toFixed(1)}
            </span>
          </div>

          <Link to={`/libros/${book.slug}`}>
            <h3 className="font-serif text-base font-semibold leading-snug line-clamp-2 group-hover:text-primary">
              {book.title}
            </h3>
          </Link>
          <p className="mt-1 text-xs text-muted-foreground line-clamp-1">{authorNames}</p>
        </div>

        <div className="mt-4 flex items-end justify-between gap-2 border-t pt-3">
          <div>
            {hasDiscount && (
              <p className="text-xs text-muted-foreground line-through">{formatPEN(book.price)}</p>
            )}
            <p className="text-base font-semibold text-primary">{formatPEN(book.final_price)}</p>
          </div>
          <Button
            size="sm"
            disabled={outOfStock}
            onClick={() => addBook(book, 1)}
            aria-label={`Agregar ${book.title} al carrito`}
          >
            <ShoppingBag className="h-4 w-4" />
            <span className="hidden sm:inline">{outOfStock ? 'Agotado' : 'Agregar'}</span>
          </Button>
        </div>
      </div>
    </article>
  )
}

export function BookCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-xl border bg-background">
      <Skeleton className="aspect-[3/4] w-full rounded-none" />
      <div className="space-y-2 p-4">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-5 w-4/5" />
        <Skeleton className="h-3 w-1/2" />
        <div className="flex items-center justify-between pt-3">
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
    </div>
  )
}
