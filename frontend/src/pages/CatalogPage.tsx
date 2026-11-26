import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { toast } from 'sonner'
import { catalogApi, favoritesApi } from '@/services/booklyApi'
import { useAuthStore } from '@/stores/useAuthStore'
import { BookCard, BookCardSkeleton } from '@/components/books/BookCard'
import { EmptyState } from '@/components/shared/EmptyState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function CatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const session = useAuthStore((s) => s.session)
  const queryClient = useQueryClient()

  const search = searchParams.get('search') || ''
  const category = searchParams.get('category') || ''
  const authorId = searchParams.get('author_id') || ''
  const minPrice = searchParams.get('min_price') || ''
  const maxPrice = searchParams.get('max_price') || ''
  const inStock = searchParams.get('in_stock') === 'true'
  const onSale = searchParams.get('on_sale') === 'true'
  const sort = searchParams.get('sort') || 'newest'
  const page = Number(searchParams.get('page') || '1')

  const queryParams = useMemo(
    () => ({
      search: search || undefined,
      category: category || undefined,
      author_id: authorId || undefined,
      min_price: minPrice || undefined,
      max_price: maxPrice || undefined,
      in_stock: inStock ? true : undefined,
      on_sale: onSale ? true : undefined,
      sort,
      page,
      page_size: 12,
    }),
    [search, category, authorId, minPrice, maxPrice, inStock, onSale, sort, page],
  )

  const { data: booksData, isLoading } = useQuery({
    queryKey: ['catalog-books', queryParams],
    queryFn: () => catalogApi.getBooks(queryParams),
  })

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: () => catalogApi.getCategories(),
  })

  const { data: favorites } = useQuery({
    queryKey: ['favorites'],
    queryFn: () => favoritesApi.list(),
    enabled: Boolean(session),
  })

  const favIds = new Set((favorites || []).map((b) => b.id))
  const favMutation = useMutation({
    mutationFn: async (bookId: string) =>
      favIds.has(bookId) ? favoritesApi.remove(bookId) : favoritesApi.add(bookId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
      toast.success('Favoritos actualizados')
    },
  })

  const updateParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.set('page', '1')
    setSearchParams(next)
  }

  const clearFilters = () => {
    setSearchParams({})
  }

  return (
    <div className="container py-10 space-y-8">
      <div className="flex flex-col justify-between gap-4 border-b pb-6 md:flex-row md:items-end">
        <div>
          <p className="text-xs uppercase tracking-widest text-bookly-gold font-semibold">
            Librería BOOKLY
          </p>
          <h1 className="font-serif text-3xl font-bold sm:text-4xl">Catálogo de libros</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {booksData?.meta.total ?? 0} títulos encontrados
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => updateParam('search', e.target.value || null)}
              placeholder="Título, autor o ISBN..."
              className="pl-9"
            />
          </div>
          <select
            value={sort}
            onChange={(e) => updateParam('sort', e.target.value)}
            aria-label="Ordenar catálogo"
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="newest">Más recientes</option>
            <option value="best_sellers">Más vendidos</option>
            <option value="rating">Mejor valorados</option>
            <option value="price_asc">Menor precio</option>
            <option value="price_desc">Mayor precio</option>
            <option value="title">Título A-Z</option>
          </select>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-12">
        {/* Filtros laterales */}
        <aside className="space-y-6 lg:col-span-3">
          <div className="rounded-xl border bg-card/40 p-5 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-serif text-lg font-semibold">
                <SlidersHorizontal className="h-4 w-4" />
                Filtros
              </h2>
              <button
                type="button"
                onClick={clearFilters}
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary"
              >
                <X className="h-3.5 w-3.5" />
                Limpiar
              </button>
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Categoría
              </p>
              <div className="flex flex-col space-y-1">
                <button
                  type="button"
                  onClick={() => updateParam('category', null)}
                  className={`rounded-md px-2.5 py-1.5 text-left text-sm transition ${
                    !category ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                  }`}
                >
                  Todas las categorías
                </button>
                {(categoriesData?.items || []).map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => updateParam('category', cat.slug)}
                    className={`rounded-md px-2.5 py-1.5 text-left text-sm transition ${
                      category === cat.slug
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2 border-t pt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Rango de precio (S/)
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  type="number"
                  min={0}
                  placeholder="Mín."
                  value={minPrice}
                  onChange={(e) => updateParam('min_price', e.target.value || null)}
                />
                <Input
                  type="number"
                  min={0}
                  placeholder="Máx."
                  value={maxPrice}
                  onChange={(e) => updateParam('max_price', e.target.value || null)}
                />
              </div>
            </div>

            <div className="space-y-2 border-t pt-4 text-sm">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={inStock}
                  onChange={(e) => updateParam('in_stock', e.target.checked ? 'true' : null)}
                  className="rounded border-input"
                />
                Solo disponibles en stock
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={onSale}
                  onChange={(e) => updateParam('on_sale', e.target.checked ? 'true' : null)}
                  className="rounded border-input"
                />
                Con descuento activo
              </label>
            </div>
          </div>
        </aside>

        {/* Resultados */}
        <div className="space-y-8 lg:col-span-9">
          {isLoading ? (
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, idx) => (
                <BookCardSkeleton key={idx} />
              ))}
            </div>
          ) : !booksData || booksData.items.length === 0 ? (
            <EmptyState
              title="No encontramos libros con esos criterios"
              description="Prueba limpiando algunos filtros o buscando otro título, autor o ISBN."
              actionLabel="Restablecer catálogo"
              onAction={clearFilters}
            />
          ) : (
            <>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {booksData.items.map((book) => (
                  <BookCard
                    key={book.id}
                    book={book}
                    isFavorite={favIds.has(book.id)}
                    onToggleFavorite={(id) => {
                      if (!session) {
                        toast.info('Inicia sesión para agregar favoritos')
                        return
                      }
                      favMutation.mutate(id)
                    }}
                  />
                ))}
              </div>

              {booksData.meta.total_pages > 1 && (
                <div className="flex items-center justify-center gap-3 pt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => updateParam('page', String(page - 1))}
                  >
                    Anterior
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Página {booksData.meta.page} de {booksData.meta.total_pages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= booksData.meta.total_pages}
                    onClick={() => updateParam('page', String(page + 1))}
                  >
                    Siguiente
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
