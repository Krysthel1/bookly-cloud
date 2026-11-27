import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Edit, Eye, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { adminApi, catalogApi } from '@/services/booklyApi'
import { extractApiError } from '@/lib/api'
import { formatDatePE, formatPEN, ORDER_STATUS_LABELS, PAYMENT_METHOD_LABELS } from '@/lib/utils'
import type { Author, Category, Order } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input, Textarea } from '@/components/ui/input'

export function AdminCategoriesPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [editing, setEditing] = useState<Category | null>(null)

  const { data } = useQuery({
    queryKey: ['admin-categories', search, page],
    queryFn: () => catalogApi.getCategories({ search: search || undefined, page, page_size: 12 }),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      editing
        ? adminApi.updateCategory(editing.id, { name, description })
        : adminApi.createCategory({ name, description }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setEditing(null)
      setName('')
      setDescription('')
      toast.success(editing ? 'Categoría actualizada' : 'Categoría creada')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      toast.success('Categoría desactivada')
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-serif text-3xl font-bold">Categorías</h1>
        <Input
          placeholder="Buscar categoría..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="max-w-xs"
        />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          createMutation.mutate()
        }}
        className="flex flex-wrap gap-3 rounded-xl border bg-card/40 p-4"
      >
        <Input
          required
          placeholder="Nombre de categoría"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="max-w-xs"
        />
        <Input
          placeholder="Descripción breve"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="flex-1 min-w-[220px]"
        />
        <Button type="submit">{editing ? 'Actualizar' : 'Agregar'}</Button>
        {editing && (
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setEditing(null)
              setName('')
              setDescription('')
            }}
          >
            Cancelar
          </Button>
        )}
      </form>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(data?.items || []).map((cat) => (
          <div key={cat.id} className="flex items-start justify-between rounded-xl border p-4">
            <div>
              <p className="font-semibold">{cat.name}</p>
              <p className="text-xs text-muted-foreground">{cat.description}</p>
              <p className="mt-2 text-xs text-primary">{cat.books_count} libros</p>
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                aria-label="Editar categoría"
                onClick={() => {
                  setEditing(cat)
                  setName(cat.name)
                  setDescription(cat.description || '')
                }}
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Desactivar categoría"
                onClick={() => deleteMutation.mutate(cat.id)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {data && data.meta.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Anterior
          </Button>
          <span className="self-center text-xs text-muted-foreground">
            Página {data.meta.page} de {data.meta.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.meta.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  )
}

export function AdminAuthorsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [name, setName] = useState('')
  const [nationality, setNationality] = useState('')
  const [biography, setBiography] = useState('')
  const [editing, setEditing] = useState<Author | null>(null)

  const { data } = useQuery({
    queryKey: ['admin-authors', search, page],
    queryFn: () => catalogApi.getAuthors({ search: search || undefined, page, page_size: 12 }),
  })

  const saveMutation = useMutation({
    mutationFn: () =>
      editing
        ? adminApi.updateAuthor(editing.id, { name, nationality, biography })
        : adminApi.createAuthor({ name, nationality, biography }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-authors'] })
      queryClient.invalidateQueries({ queryKey: ['authors-all'] })
      setEditing(null)
      setName('')
      setNationality('')
      setBiography('')
      toast.success(editing ? 'Autor actualizado' : 'Autor creado')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteAuthor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-authors'] })
      queryClient.invalidateQueries({ queryKey: ['authors-all'] })
      toast.success('Autor desactivado')
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-serif text-3xl font-bold">Autores</h1>
        <Input
          placeholder="Buscar autor..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="max-w-xs"
        />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          saveMutation.mutate()
        }}
        className="grid gap-3 rounded-xl border bg-card/40 p-4 sm:grid-cols-3"
      >
        <Input
          required
          placeholder="Nombre del autor"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          placeholder="Nacionalidad"
          value={nationality}
          onChange={(e) => setNationality(e.target.value)}
        />
        <div className="flex gap-2">
          <Button type="submit" className="flex-1">
            {editing ? 'Actualizar autor' : 'Crear autor'}
          </Button>
          {editing && (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setEditing(null)
                setName('')
                setNationality('')
                setBiography('')
              }}
            >
              Cancelar
            </Button>
          )}
        </div>
        <Textarea
          placeholder="Biografía breve"
          value={biography}
          onChange={(e) => setBiography(e.target.value)}
          className="sm:col-span-3"
        />
      </form>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(data?.items || []).map((a) => (
          <div key={a.id} className="flex items-start justify-between rounded-xl border p-4">
            <div>
              <p className="font-semibold">{a.name}</p>
              <p className="text-xs text-muted-foreground">{a.nationality || 'Internacional'}</p>
              <p className="mt-1 text-xs text-primary">{a.books_count} títulos</p>
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                aria-label="Editar autor"
                onClick={() => {
                  setEditing(a)
                  setName(a.name)
                  setNationality(a.nationality || '')
                  setBiography(a.biography || '')
                }}
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Desactivar autor"
                onClick={() => deleteMutation.mutate(a.id)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {data && data.meta.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Anterior
          </Button>
          <span className="self-center text-xs text-muted-foreground">
            Página {data.meta.page} de {data.meta.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.meta.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  )
}

export function AdminInventoryPage() {
  const queryClient = useQueryClient()
  const [bookId, setBookId] = useState('')
  const [movementType, setMovementType] = useState<'entrada' | 'salida' | 'ajuste'>('entrada')
  const [quantity, setQuantity] = useState('5')
  const [reason, setReason] = useState('')

  const { data: inventory } = useQuery({
    queryKey: ['admin-inventory'],
    queryFn: () => adminApi.listInventory({ page: 1 }),
  })
  const { data: movements } = useQuery({
    queryKey: ['admin-movements'],
    queryFn: () => adminApi.listMovements(1),
  })

  const movementMutation = useMutation({
    mutationFn: () =>
      adminApi.createMovement({
        book_id: bookId,
        movement_type: movementType,
        quantity: Number(quantity),
        reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-inventory'] })
      queryClient.invalidateQueries({ queryKey: ['admin-movements'] })
      setReason('')
      toast.success('Movimiento registrado')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  return (
    <div className="space-y-8">
      <h1 className="font-serif text-3xl font-bold">Gestión de inventario</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          movementMutation.mutate()
        }}
        className="grid gap-3 rounded-xl border bg-card/40 p-5 sm:grid-cols-5"
      >
        <select
          required
          value={bookId}
          onChange={(e) => setBookId(e.target.value)}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm sm:col-span-2"
        >
          <option value="">Selecciona libro...</option>
          {(inventory?.items || []).map((b) => (
            <option key={b.id} value={b.id}>
              {b.title} (Stock: {b.stock})
            </option>
          ))}
        </select>
        <select
          value={movementType}
          onChange={(e) => setMovementType(e.target.value as 'entrada' | 'salida' | 'ajuste')}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="entrada">Entrada (+)</option>
          <option value="salida">Salida (-)</option>
          <option value="ajuste">Ajuste exacto</option>
        </select>
        <Input
          type="number"
          min="0"
          required
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="Cantidad"
        />
        <Button type="submit" disabled={movementMutation.isPending}>
          Registrar
        </Button>
        <Input
          required
          minLength={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Motivo del movimiento (ej. Reposición editorial)"
          className="sm:col-span-5"
        />
      </form>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border overflow-hidden">
          <h2 className="border-b bg-card/60 p-4 font-serif text-lg font-semibold">Stock actual</h2>
          <div className="max-h-96 overflow-y-auto divide-y text-sm">
            {(inventory?.items || []).map((b) => (
              <div key={b.id} className="flex items-center justify-between p-3">
                <div>
                  <p className="font-medium">{b.title}</p>
                  <p className="text-xs text-muted-foreground">ISBN {b.isbn}</p>
                </div>
                <Badge
                  variant={
                    b.stock === 0
                      ? 'destructive'
                      : b.stock <= b.low_stock_threshold
                        ? 'gold'
                        : 'secondary'
                  }
                >
                  {b.stock} uds • {b.status_label}
                </Badge>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border overflow-hidden">
          <h2 className="border-b bg-card/60 p-4 font-serif text-lg font-semibold">
            Historial de movimientos
          </h2>
          <div className="max-h-96 overflow-y-auto divide-y text-sm">
            {(movements?.items || []).map((m) => (
              <div key={m.id} className="p-3 space-y-1">
                <div className="flex justify-between">
                  <span className="font-medium">{m.book_title}</span>
                  <span className="font-mono text-xs">
                    {m.previous_stock} → {m.new_stock} ({m.quantity_delta >= 0 ? '+' : ''}
                    {m.quantity_delta})
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {m.movement_type.toUpperCase()} • {m.reason} • Por: {m.performer_name}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export function AdminOrdersPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')
  const [detailOrder, setDetailOrder] = useState<Order | null>(null)

  const { data } = useQuery({
    queryKey: ['admin-orders', statusFilter],
    queryFn: () => adminApi.listOrders({ status: statusFilter || undefined }),
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      adminApi.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders'] })
      toast.success('Estado del pedido actualizado')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const nextTransitions: Record<string, string[]> = {
    pendiente: ['confirmado', 'cancelado'],
    confirmado: ['en_preparacion', 'cancelado'],
    en_preparacion: ['enviado', 'cancelado'],
    enviado: ['entregado'],
    entregado: [],
    cancelado: [],
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-serif text-3xl font-bold">Gestión de pedidos</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">Todos los estados</option>
          {Object.entries(ORDER_STATUS_LABELS).map(([k, label]) => (
            <option key={k} value={k}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-card/60 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="p-3">Código</th>
              <th className="p-3">Cliente</th>
              <th className="p-3">Fecha</th>
              <th className="p-3">Total</th>
              <th className="p-3">Estado</th>
              <th className="p-3">Cambiar estado</th>
              <th className="p-3 text-right">Detalle</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(data?.items || []).map((o) => {
              const options = nextTransitions[o.status] || []
              return (
                <tr key={o.id}>
                  <td className="p-3 font-mono font-semibold">{o.order_code}</td>
                  <td className="p-3">{o.customer_email || o.customer_name}</td>
                  <td className="p-3 text-xs">{formatDatePE(o.created_at)}</td>
                  <td className="p-3 font-semibold">{formatPEN(o.total)}</td>
                  <td className="p-3">
                    <Badge variant={o.status === 'cancelado' ? 'destructive' : 'secondary'}>
                      {ORDER_STATUS_LABELS[o.status] || o.status}
                    </Badge>
                  </td>
                  <td className="p-3">
                    {options.length > 0 ? (
                      <select
                        defaultValue=""
                        onChange={(e) => {
                          if (e.target.value) {
                            statusMutation.mutate({ id: o.id, status: e.target.value })
                          }
                        }}
                        className="h-8 rounded border bg-background px-2 text-xs"
                      >
                        <option value="" disabled>
                          Mover a...
                        </option>
                        {options.map((st) => (
                          <option key={st} value={st}>
                            {ORDER_STATUS_LABELS[st]}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-xs text-muted-foreground">Estado final</span>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <Button variant="ghost" size="icon" onClick={() => setDetailOrder(o)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <Dialog open={Boolean(detailOrder)} onOpenChange={(open) => !open && setDetailOrder(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Pedido {detailOrder?.order_code}</DialogTitle>
          </DialogHeader>
          {detailOrder && (
            <div className="space-y-4 text-sm">
              <div className="rounded-lg border bg-card/40 p-3 text-xs space-y-1">
                <p><strong>Cliente:</strong> {detailOrder.customer_name} ({detailOrder.customer_email})</p>
                <p><strong>Envío:</strong> {detailOrder.shipping_address_snapshot.street_address}, {detailOrder.shipping_address_snapshot.district}</p>
                <p><strong>Pago:</strong> {PAYMENT_METHOD_LABELS[detailOrder.payment?.method || ''] || '—'} ({detailOrder.payment?.status})</p>
              </div>
              <div className="space-y-2">
                {detailOrder.items.map((item) => (
                  <div key={item.id} className="flex justify-between border-b pb-1.5">
                    <span>{item.quantity}x {item.book_title_snapshot}</span>
                    <span className="font-medium">{formatPEN(item.line_total)}</span>
                  </div>
                ))}
              </div>
              <div className="flex justify-between font-bold text-base">
                <span>Total</span>
                <span className="text-primary">{formatPEN(detailOrder.total)}</span>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
