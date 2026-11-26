import { useState } from 'react'
import { Link, NavLink, Outlet, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, Heart, MapPin, Package, Settings, Trash2, User } from 'lucide-react'
import { toast } from 'sonner'
import { accountApi, favoritesApi, ordersApi } from '@/services/booklyApi'
import { useAuthStore } from '@/stores/useAuthStore'
import { extractApiError } from '@/lib/api'
import { formatDatePE, formatPEN, ORDER_STATUS_LABELS, PAYMENT_METHOD_LABELS } from '@/lib/utils'
import { BookCard } from '@/components/books/BookCard'
import { ConfirmModal } from '@/components/shared/ConfirmModal'
import { EmptyState } from '@/components/shared/EmptyState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/card'

export function AccountLayout() {
  const navItems = [
    { to: '/mi-cuenta', label: 'Perfil personal', icon: User, end: true },
    { to: '/mi-cuenta/pedidos', label: 'Mis pedidos', icon: Package },
    { to: '/mi-cuenta/direcciones', label: 'Direcciones', icon: MapPin },
    { to: '/mi-cuenta/favoritos', label: 'Favoritos', icon: Heart },
    { to: '/mi-cuenta/notificaciones', label: 'Notificaciones', icon: Bell },
    { to: '/mi-cuenta/configuracion', label: 'Configuración', icon: Settings },
  ]

  return (
    <div className="container py-10">
      <h1 className="mb-6 font-serif text-3xl font-bold">Mi cuenta</h1>
      <div className="grid gap-8 lg:grid-cols-12">
        <aside className="lg:col-span-3">
          <nav className="flex flex-col gap-1 rounded-xl border bg-card/40 p-3">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition ${
                      isActive ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>
        </aside>
        <div className="lg:col-span-9">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export function AccountProfilePage() {
  const { profile, fetchProfile } = useAuthStore()
  const [fullName, setFullName] = useState(profile?.full_name || '')
  const [phone, setPhone] = useState(profile?.phone || '')

  const updateMutation = useMutation({
    mutationFn: () => accountApi.updateProfile({ full_name: fullName, phone }),
    onSuccess: async () => {
      await fetchProfile()
      toast.success('Perfil actualizado correctamente')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  return (
    <div className="rounded-xl border bg-card/40 p-6 space-y-5">
      <h2 className="font-serif text-2xl font-semibold">Información personal</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          updateMutation.mutate()
        }}
        className="max-w-lg space-y-4"
      >
        <div className="space-y-1.5">
          <Label>Correo electrónico</Label>
          <Input value={profile?.email || ''} disabled />
        </div>
        <div className="space-y-1.5">
          <Label>Nombre completo</Label>
          <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Teléfono</Label>
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="999 888 777" />
        </div>
        <Button type="submit" disabled={updateMutation.isPending}>
          {updateMutation.isPending ? 'Guardando...' : 'Guardar cambios'}
        </Button>
      </form>
    </div>
  )
}

export function AccountAddressesPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    label: 'Casa',
    recipient_name: '',
    phone: '',
    street_address: '',
    district: '',
    city: 'Lima',
    region: 'Lima',
    postal_code: '',
    reference: '',
    is_default: true,
  })

  const { data: addresses } = useQuery({
    queryKey: ['my-addresses'],
    queryFn: () => accountApi.listAddresses(),
  })

  const createMutation = useMutation({
    mutationFn: () => accountApi.createAddress(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-addresses'] })
      toast.success('Dirección agregada')
      setForm({
        ...form,
        street_address: '',
        district: '',
        reference: '',
      })
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => accountApi.deleteAddress(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-addresses'] })
      toast.success('Dirección eliminada')
    },
  })

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        {(addresses || []).map((addr) => (
          <div key={addr.id} className="rounded-xl border bg-card/40 p-4 space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{addr.label}</span>
                {addr.is_default && <Badge variant="gold">Principal</Badge>}
              </div>
              <Button variant="ghost" size="icon" onClick={() => deleteMutation.mutate(addr.id)}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
            <p className="text-sm">{addr.recipient_name} • {addr.phone}</p>
            <p className="text-xs text-muted-foreground">{addr.street_address}</p>
            <p className="text-xs text-muted-foreground">
              {addr.district}, {addr.city}, {addr.region}
            </p>
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          createMutation.mutate()
        }}
        className="rounded-xl border bg-card/40 p-6 space-y-4"
      >
        <h3 className="font-serif text-xl font-semibold">Agregar nueva dirección</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <Input
            placeholder="Etiqueta (Casa, Oficina)"
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
            required
          />
          <Input
            placeholder="Nombre destinatario"
            value={form.recipient_name}
            onChange={(e) => setForm({ ...form, recipient_name: e.target.value })}
            required
          />
          <Input
            placeholder="Teléfono"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            required
          />
          <Input
            placeholder="Dirección"
            value={form.street_address}
            onChange={(e) => setForm({ ...form, street_address: e.target.value })}
            required
          />
          <Input
            placeholder="Distrito"
            value={form.district}
            onChange={(e) => setForm({ ...form, district: e.target.value })}
            required
          />
          <Input
            placeholder="Ciudad"
            value={form.city}
            onChange={(e) => setForm({ ...form, city: e.target.value })}
            required
          />
        </div>
        <Button type="submit" disabled={createMutation.isPending}>
          Guardar dirección
        </Button>
      </form>
    </div>
  )
}

export function AccountOrdersPage() {
  const { data } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => ordersApi.listMine(1),
  })

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={Package}
        title="Aún no tienes pedidos"
        description="Cuando realices una compra podrás hacer seguimiento aquí."
      />
    )
  }

  return (
    <div className="space-y-4">
      {data.items.map((order) => (
        <Link
          key={order.id}
          to={`/mi-cuenta/pedidos/${order.id}`}
          className="flex flex-col justify-between gap-3 rounded-xl border bg-card/40 p-5 transition hover:border-primary/40 sm:flex-row sm:items-center"
        >
          <div>
            <p className="font-mono text-sm font-bold">{order.order_code}</p>
            <p className="text-xs text-muted-foreground">
              {formatDatePE(order.created_at)} • {order.items.length} libro(s)
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant={order.status === 'cancelado' ? 'destructive' : 'secondary'}>
              {ORDER_STATUS_LABELS[order.status] || order.status}
            </Badge>
            <span className="font-semibold text-primary">{formatPEN(order.total)}</span>
          </div>
        </Link>
      ))}
    </div>
  )
}

export function AccountOrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>()
  const queryClient = useQueryClient()
  const [confirmOpen, setConfirmOpen] = useState(false)

  const { data: order } = useQuery({
    queryKey: ['my-order', orderId],
    queryFn: () => ordersApi.getDetail(orderId!),
    enabled: Boolean(orderId),
  })

  const cancelMutation = useMutation({
    mutationFn: () => ordersApi.cancelOrder(orderId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-order', orderId] })
      queryClient.invalidateQueries({ queryKey: ['my-orders'] })
      setConfirmOpen(false)
      toast.success('Pedido cancelado y stock restaurado')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  if (!order) return <p className="text-sm text-muted-foreground">Cargando pedido...</p>

  const canCancel = order.status === 'pendiente' || order.status === 'confirmado'

  return (
    <div className="rounded-xl border bg-card/40 p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-4">
        <div>
          <p className="font-mono text-lg font-bold">{order.order_code}</p>
          <p className="text-xs text-muted-foreground">{formatDatePE(order.created_at)}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={order.status === 'cancelado' ? 'destructive' : 'gold'}>
            {ORDER_STATUS_LABELS[order.status] || order.status}
          </Badge>
          {canCancel && (
            <Button variant="destructive" size="sm" onClick={() => setConfirmOpen(true)}>
              Cancelar pedido
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {order.items.map((item) => (
          <div key={item.id} className="flex justify-between text-sm">
            <span>
              {item.quantity}x {item.book_title_snapshot}
            </span>
            <span className="font-medium">{formatPEN(item.line_total)}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-4 border-t pt-4 text-sm sm:grid-cols-2">
        <div>
          <p className="font-semibold">Dirección de envío</p>
          <p className="text-xs text-muted-foreground">
            {order.shipping_address_snapshot.recipient_name} •{' '}
            {order.shipping_address_snapshot.street_address},{' '}
            {order.shipping_address_snapshot.district}
          </p>
        </div>
        <div className="space-y-1 text-right">
          <p className="text-xs text-muted-foreground">
            Pago: {PAYMENT_METHOD_LABELS[order.payment?.method || ''] || '—'}
          </p>
          <p className="font-bold text-primary">Total: {formatPEN(order.total)}</p>
        </div>
      </div>

      <ConfirmModal
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="¿Cancelar pedido?"
        description="Esta acción cancelará tu pedido y devolverá las unidades al inventario."
        confirmLabel="Sí, cancelar pedido"
        destructive
        loading={cancelMutation.isPending}
        onConfirm={() => cancelMutation.mutate()}
      />
    </div>
  )
}

export function AccountFavoritesPage() {
  const queryClient = useQueryClient()
  const { data: favorites } = useQuery({
    queryKey: ['favorites'],
    queryFn: () => favoritesApi.list(),
  })

  if (!favorites || favorites.length === 0) {
    return (
      <EmptyState
        icon={Heart}
        title="Sin libros favoritos"
        description="Guarda tus libros preferidos desde el catálogo para verlos aquí."
      />
    )
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
      {favorites.map((book) => (
        <BookCard
          key={book.id}
          book={book}
          isFavorite
          onToggleFavorite={(id) => {
            favoritesApi.remove(id).then(() => {
              queryClient.invalidateQueries({ queryKey: ['favorites'] })
              toast.success('Eliminado de favoritos')
            })
          }}
        />
      ))}
    </div>
  )
}

export function AccountNotificationsPage() {
  const queryClient = useQueryClient()
  const { data: notifications } = useQuery({
    queryKey: ['my-notifications'],
    queryFn: () => accountApi.listNotifications(),
  })

  if (!notifications || notifications.length === 0) {
    return (
      <EmptyState
        icon={Bell}
        title="Sin notificaciones"
        description="Aquí recibirás actualizaciones sobre tus pedidos y promociones."
      />
    )
  }

  return (
    <div className="space-y-3">
      {notifications.map((n) => (
        <div
          key={n.id}
          className={`flex items-start justify-between gap-4 rounded-xl border p-4 ${
            n.is_read ? 'bg-card/20' : 'border-primary/40 bg-card/70'
          }`}
        >
          <div>
            <p className="font-semibold text-sm">{n.title}</p>
            <p className="text-xs text-muted-foreground">{n.message}</p>
            <p className="mt-1 text-[11px] text-muted-foreground">{formatDatePE(n.created_at)}</p>
          </div>
          {!n.is_read && (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                accountApi.markNotificationRead(n.id).then(() => {
                  queryClient.invalidateQueries({ queryKey: ['my-notifications'] })
                })
              }
            >
              Marcar leída
            </Button>
          )}
        </div>
      ))}
    </div>
  )
}

export function AccountSettingsPage() {
  const signOut = useAuthStore((s) => s.signOut)
  return (
    <div className="rounded-xl border bg-card/40 p-6 space-y-4">
      <h2 className="font-serif text-2xl font-semibold">Configuración de cuenta</h2>
      <p className="text-sm text-muted-foreground">
        Gestiona tu sesión activa o solicita el restablecimiento de tu contraseña mediante Supabase
        Auth.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button variant="outline" asChild>
          <Link to="/recuperar-contrasena">Cambiar contraseña</Link>
        </Button>
        <Button variant="destructive" onClick={() => signOut()}>
          Cerrar sesión
        </Button>
      </div>
    </div>
  )
}
