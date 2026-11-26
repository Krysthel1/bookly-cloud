import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Minus, Plus, ShoppingBag, Tag, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { useCartStore } from '@/stores/useCartStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { ordersApi } from '@/services/booklyApi'
import { extractApiError } from '@/lib/api'
import { formatPEN } from '@/lib/utils'
import { EmptyState } from '@/components/shared/EmptyState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { CouponValidation } from '@/types'

export function CartPage() {
  const navigate = useNavigate()
  const session = useAuthStore((s) => s.session)
  const { items, subtotal, updateQuantity, removeItem } = useCartStore()
  const [couponCode, setCouponCode] = useState('')
  const [appliedCoupon, setAppliedCoupon] = useState<CouponValidation | null>(null)
  const [validatingCoupon, setValidatingCoupon] = useState(false)

  const discountAmount = appliedCoupon ? Number(appliedCoupon.discount_amount) : 0
  const netSubtotal = Math.max(0, subtotal - discountAmount)
  const shippingCost = netSubtotal >= 120 || netSubtotal === 0 ? 0 : 12
  const estimatedTotal = netSubtotal + shippingCost

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!session) {
      toast.info('Inicia sesión para validar cupones promocionales')
      return
    }
    if (!couponCode.trim()) return
    setValidatingCoupon(true)
    try {
      const res = await ordersApi.validateCoupon(couponCode.trim(), subtotal)
      setAppliedCoupon(res)
      toast.success(res.message)
    } catch (err) {
      setAppliedCoupon(null)
      toast.error(extractApiError(err))
    } finally {
      setValidatingCoupon(false)
    }
  }

  if (items.length === 0) {
    return (
      <div className="container py-16">
        <EmptyState
          icon={ShoppingBag}
          title="Tu carrito está vacío"
          description="Explora nuestro catálogo curado y agrega tus próximas lecturas."
          actionLabel="Explorar catálogo"
          onAction={() => navigate('/catalogo')}
        />
      </div>
    )
  }

  return (
    <div className="container py-10 space-y-8">
      <div className="flex flex-col justify-between gap-2 border-b pb-5 sm:flex-row sm:items-end">
        <div>
          <h1 className="font-serif text-3xl font-bold">Carrito de compras</h1>
          <p className="text-sm text-muted-foreground">
            {session ? 'Tu carrito está sincronizado con tu cuenta.' : 'Inicia sesión al finalizar para guardar tu pedido.'}
          </p>
        </div>
        <Link to="/catalogo" className="text-sm font-medium text-primary hover:underline">
          ← Seguir comprando
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-8">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col gap-4 rounded-xl border bg-card/40 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="h-24 w-16 shrink-0 overflow-hidden rounded-md bg-bookly-forest text-bookly-cream flex items-center justify-center text-[10px] p-1 text-center">
                  {item.book.cover_url ? (
                    <img
                      src={item.book.cover_url}
                      alt={item.book.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    item.book.title
                  )}
                </div>
                <div>
                  <Link
                    to={`/libros/${item.book.slug}`}
                    className="font-serif text-lg font-semibold hover:text-primary"
                  >
                    {item.book.title}
                  </Link>
                  <p className="text-xs text-muted-foreground">
                    {item.book.authors.join(', ')} • Stock: {item.book.stock}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-primary">
                    {formatPEN(item.book.final_price)} c/u
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between gap-4 sm:justify-end">
                <div className="flex items-center rounded-md border bg-background">
                  <Button
                    variant="ghost"
                    size="icon"
                    disabled={item.quantity <= 1}
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    aria-label="Reducir cantidad"
                  >
                    <Minus className="h-3.5 w-3.5" />
                  </Button>
                  <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    disabled={item.quantity >= item.book.stock}
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    aria-label="Aumentar cantidad"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </Button>
                </div>

                <p className="w-24 text-right font-semibold">
                  {formatPEN(Number(item.book.final_price) * item.quantity)}
                </p>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeItem(item.id)}
                  aria-label="Eliminar del carrito"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        <aside className="lg:col-span-4">
          <div className="rounded-2xl border bg-card/60 p-6 space-y-5">
            <h2 className="font-serif text-xl font-bold">Resumen del pedido</h2>

            <form onSubmit={handleApplyCoupon} className="flex gap-2">
              <div className="relative flex-1">
                <Tag className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  placeholder="Cupón (ej. BOOKLY10)"
                  className="pl-9 bg-background"
                />
              </div>
              <Button type="submit" variant="outline" disabled={validatingCoupon}>
                Aplicar
              </Button>
            </form>

            <div className="space-y-2 border-t pt-4 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span>{formatPEN(subtotal)}</span>
              </div>
              {discountAmount > 0 && (
                <div className="flex justify-between text-emerald-700 dark:text-emerald-400">
                  <span>Descuento ({appliedCoupon?.code})</span>
                  <span>-{formatPEN(discountAmount)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Envío estándar</span>
                <span>{shippingCost === 0 ? 'Gratis' : formatPEN(shippingCost)}</span>
              </div>
              <div className="flex justify-between border-t pt-3 text-base font-bold">
                <span>Total estimado</span>
                <span className="text-primary">{formatPEN(estimatedTotal)}</span>
              </div>
            </div>

            <Button
              size="lg"
              className="w-full"
              onClick={() =>
                navigate('/checkout', {
                  state: { couponCode: appliedCoupon?.code || '' },
                })
              }
            >
              Finalizar compra
            </Button>
          </div>
        </aside>
      </div>
    </div>
  )
}
