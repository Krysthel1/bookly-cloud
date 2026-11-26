import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, CreditCard, MapPin, PackageCheck, ShieldCheck, Truck, User } from 'lucide-react'
import { toast } from 'sonner'
import { accountApi, ordersApi } from '@/services/booklyApi'
import { useAuthStore } from '@/stores/useAuthStore'
import { useCartStore } from '@/stores/useCartStore'
import { extractApiError } from '@/lib/api'
import { formatPEN, PAYMENT_METHOD_LABELS } from '@/lib/utils'
import type { Order } from '@/types'
import { Button } from '@/components/ui/button'
import { Input, Textarea } from '@/components/ui/input'
import { Label } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const STEPS = [
  { id: 1, title: 'Datos personales', icon: User },
  { id: 2, title: 'Dirección de entrega', icon: MapPin },
  { id: 3, title: 'Método de envío', icon: Truck },
  { id: 4, title: 'Método de pago', icon: CreditCard },
  { id: 5, title: 'Confirmación', icon: PackageCheck },
]

export function CheckoutPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const profile = useAuthStore((s) => s.profile)
  const { items, subtotal, fetchCart } = useCartStore()

  const initialCoupon = (location.state as { couponCode?: string } | null)?.couponCode || ''

  const [step, setStep] = useState(1)
  const [recipientName, setRecipientName] = useState(profile?.full_name || '')
  const [phone, setPhone] = useState(profile?.phone || '')
  const [selectedAddressId, setSelectedAddressId] = useState<string>('')
  const [newAddress, setNewAddress] = useState({
    street_address: '',
    district: '',
    city: 'Lima',
    region: 'Lima',
    postal_code: '',
    reference: '',
  })
  const [shippingMethod, setShippingMethod] = useState<'estandar' | 'express' | 'recojo_tienda'>('estandar')
  const [paymentMethod, setPaymentMethod] = useState<'tarjeta' | 'yape' | 'plin' | 'contra_entrega'>('tarjeta')
  const [couponCode, setCouponCode] = useState(initialCoupon)
  const [couponDiscount, setCouponDiscount] = useState(0)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [confirmedOrder, setConfirmedOrder] = useState<Order | null>(null)
  const [idempotencyKey] = useState(() => `bkl-${crypto.randomUUID()}`)

  const { data: addresses } = useQuery({
    queryKey: ['my-addresses'],
    queryFn: () => accountApi.listAddresses(),
  })

  useEffect(() => {
    if (profile) {
      if (!recipientName) setRecipientName(profile.full_name)
      if (!phone && profile.phone) setPhone(profile.phone)
    }
  }, [profile, recipientName, phone])

  useEffect(() => {
    if (addresses && addresses.length > 0 && !selectedAddressId) {
      const def = addresses.find((a) => a.is_default) || addresses[0]
      setSelectedAddressId(def.id)
    }
  }, [addresses, selectedAddressId])

  useEffect(() => {
    if (initialCoupon && subtotal > 0) {
      ordersApi
        .validateCoupon(initialCoupon, subtotal)
        .then((res) => setCouponDiscount(Number(res.discount_amount)))
        .catch(() => setCouponDiscount(0))
    }
  }, [initialCoupon, subtotal])

  const netSubtotal = Math.max(0, subtotal - couponDiscount)
  const shippingCost =
    shippingMethod === 'recojo_tienda'
      ? 0
      : shippingMethod === 'express'
        ? 22
        : netSubtotal >= 120
          ? 0
          : 12
  const estimatedTotal = netSubtotal + shippingCost

  const handleConfirmOrder = async () => {
    setSubmitting(true)
    try {
      const payload = {
        ...(selectedAddressId && selectedAddressId !== 'new'
          ? { address_id: selectedAddressId }
          : {
              shipping_address: {
                recipient_name: recipientName,
                phone,
                ...newAddress,
              },
            }),
        shipping_method: shippingMethod,
        payment_method: paymentMethod,
        coupon_code: couponCode.trim() || undefined,
        notes: notes.trim() || undefined,
        idempotency_key: idempotencyKey,
      }
      const order = await ordersApi.checkout(payload)
      setConfirmedOrder(order)
      setStep(5)
      await fetchCart()
      toast.success(`Pedido ${order.order_code} confirmado`)
    } catch (err) {
      toast.error(extractApiError(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (items.length === 0 && !confirmedOrder) {
    return (
      <div className="container py-16 text-center space-y-4">
        <h1 className="font-serif text-3xl font-bold">No hay productos para procesar</h1>
        <Button onClick={() => navigate('/catalogo')}>Explorar catálogo</Button>
      </div>
    )
  }

  return (
    <div className="container py-10 space-y-8">
      <div>
        <h1 className="font-serif text-3xl font-bold">Finalizar compra</h1>
        <p className="text-sm text-muted-foreground">
          Proceso de compra seguro y validado en servidor (pagos simulados).
        </p>
      </div>

      {/* Stepper */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {STEPS.map((s) => {
          const Icon = s.icon
          const active = step === s.id
          const done = step > s.id
          return (
            <div
              key={s.id}
              className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 text-xs font-medium transition ${
                active
                  ? 'border-primary bg-primary text-primary-foreground'
                  : done
                    ? 'border-primary/30 bg-primary/10 text-primary'
                    : 'bg-card/40 text-muted-foreground'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{s.id}. {s.title}</span>
            </div>
          )
        })}
      </div>

      {step === 5 && confirmedOrder ? (
        <div className="mx-auto max-w-2xl rounded-2xl border bg-card/50 p-8 text-center space-y-5">
          <CheckCircle2 className="mx-auto h-14 w-14 text-emerald-600" />
          <Badge variant="gold">Pedido confirmado</Badge>
          <h2 className="font-serif text-3xl font-bold">¡Gracias por tu compra!</h2>
          <p className="text-sm text-muted-foreground">
            Código único de pedido:{' '}
            <strong className="text-foreground font-mono text-base">{confirmedOrder.order_code}</strong>
          </p>
          <div className="rounded-xl border bg-background p-4 text-left text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Estado del pedido:</span>
              <span className="font-medium capitalize">{confirmedOrder.status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Método de pago simulado:</span>
              <span className="font-medium">
                {PAYMENT_METHOD_LABELS[confirmedOrder.payment?.method || ''] || confirmedOrder.payment?.method}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Referencia transaccional:</span>
              <span className="font-mono text-xs">{confirmedOrder.payment?.transaction_reference}</span>
            </div>
            <div className="flex justify-between border-t pt-2 font-bold">
              <span>Total pagado:</span>
              <span className="text-primary">{formatPEN(confirmedOrder.total)}</span>
            </div>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            <Button asChild>
              <Link to={`/mi-cuenta/pedidos/${confirmedOrder.id}`}>Seguir mi pedido</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/catalogo">Seguir explorando</Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-12">
          <div className="space-y-6 rounded-2xl border bg-card/40 p-6 lg:col-span-8">
            {step === 1 && (
              <div className="space-y-4">
                <h2 className="font-serif text-xl font-semibold">1. Datos personales</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>Nombre del destinatario</Label>
                    <Input
                      value={recipientName}
                      onChange={(e) => setRecipientName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Teléfono de contacto</Label>
                    <Input
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="999 888 777"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Correo de confirmación</Label>
                  <Input value={profile?.email || ''} disabled />
                </div>
                <div className="flex justify-end">
                  <Button
                    onClick={() => {
                      if (!recipientName.trim() || phone.trim().length < 6) {
                        toast.error('Completa tu nombre y teléfono válido')
                        return
                      }
                      setStep(2)
                    }}
                  >
                    Continuar a dirección
                  </Button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <h2 className="font-serif text-xl font-semibold">2. Dirección de entrega</h2>
                {addresses && addresses.length > 0 && (
                  <div className="space-y-2">
                    <Label>Direcciones guardadas</Label>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {addresses.map((addr) => (
                        <button
                          key={addr.id}
                          type="button"
                          onClick={() => setSelectedAddressId(addr.id)}
                          className={`rounded-xl border p-3 text-left text-sm transition ${
                            selectedAddressId === addr.id
                              ? 'border-primary bg-primary/10'
                              : 'bg-background hover:bg-muted'
                          }`}
                        >
                          <p className="font-semibold">{addr.label}</p>
                          <p className="text-xs text-muted-foreground">{addr.street_address}</p>
                          <p className="text-xs text-muted-foreground">
                            {addr.district}, {addr.city}
                          </p>
                        </button>
                      ))}
                      <button
                        type="button"
                        onClick={() => setSelectedAddressId('new')}
                        className={`rounded-xl border border-dashed p-3 text-left text-sm ${
                          selectedAddressId === 'new' ? 'border-primary bg-primary/10' : ''
                        }`}
                      >
                        + Usar otra dirección
                      </button>
                    </div>
                  </div>
                )}

                {(!addresses || addresses.length === 0 || selectedAddressId === 'new') && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="sm:col-span-2 space-y-1.5">
                      <Label>Dirección exacta</Label>
                      <Input
                        value={newAddress.street_address}
                        onChange={(e) =>
                          setNewAddress({ ...newAddress, street_address: e.target.value })
                        }
                        placeholder="Av. Larco 450, Dpto 302"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Distrito</Label>
                      <Input
                        value={newAddress.district}
                        onChange={(e) => setNewAddress({ ...newAddress, district: e.target.value })}
                        placeholder="Miraflores"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Ciudad</Label>
                      <Input
                        value={newAddress.city}
                        onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Región</Label>
                      <Input
                        value={newAddress.region}
                        onChange={(e) => setNewAddress({ ...newAddress, region: e.target.value })}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Referencia (opcional)</Label>
                      <Input
                        value={newAddress.reference}
                        onChange={(e) => setNewAddress({ ...newAddress, reference: e.target.value })}
                      />
                    </div>
                  </div>
                )}

                <div className="flex justify-between pt-2">
                  <Button variant="outline" onClick={() => setStep(1)}>
                    Atrás
                  </Button>
                  <Button
                    onClick={() => {
                      if (
                        (!selectedAddressId || selectedAddressId === 'new') &&
                        (!newAddress.street_address.trim() || !newAddress.district.trim())
                      ) {
                        toast.error('Ingresa la dirección y distrito de entrega')
                        return
                      }
                      setStep(3)
                    }}
                  >
                    Continuar a envío
                  </Button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <h2 className="font-serif text-xl font-semibold">3. Método de envío</h2>
                <div className="space-y-3">
                  {[
                    {
                      id: 'estandar' as const,
                      title: 'Envío estándar (2-4 días hábiles)',
                      desc: netSubtotal >= 120 ? 'Gratis por compras desde S/ 120.00' : 'S/ 12.00 a domicilio',
                    },
                    {
                      id: 'express' as const,
                      title: 'Envío Express Lima (24 horas)',
                      desc: 'S/ 22.00 — entrega prioritaria',
                    },
                    {
                      id: 'recojo_tienda' as const,
                      title: 'Recojo en librería BOOKLY (Miraflores)',
                      desc: 'Gratis — listo en 2 horas',
                    },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setShippingMethod(opt.id)}
                      className={`flex w-full items-center justify-between rounded-xl border p-4 text-left ${
                        shippingMethod === opt.id ? 'border-primary bg-primary/10' : 'bg-background'
                      }`}
                    >
                      <div>
                        <p className="font-semibold text-sm">{opt.title}</p>
                        <p className="text-xs text-muted-foreground">{opt.desc}</p>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="space-y-1.5">
                  <Label>Notas del pedido (opcional)</Label>
                  <Textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Instrucciones de entrega..."
                  />
                </div>
                <div className="flex justify-between">
                  <Button variant="outline" onClick={() => setStep(2)}>
                    Atrás
                  </Button>
                  <Button onClick={() => setStep(4)}>Continuar a pago</Button>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <h2 className="font-serif text-xl font-semibold">4. Método de pago simulado</h2>
                <div className="rounded-lg border border-bookly-gold/50 bg-bookly-gold/10 p-3 text-xs">
                  <ShieldCheck className="mr-1.5 inline h-4 w-4 text-bookly-forest dark:text-bookly-gold" />
                  Simulación segura: BOOKLY no procesa cobros reales ni almacena datos de tarjetas.
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  {(['tarjeta', 'yape', 'plin', 'contra_entrega'] as const).map((method) => (
                    <button
                      key={method}
                      type="button"
                      onClick={() => setPaymentMethod(method)}
                      className={`rounded-xl border p-4 text-left ${
                        paymentMethod === method ? 'border-primary bg-primary/10' : 'bg-background'
                      }`}
                    >
                      <p className="font-semibold text-sm">{PAYMENT_METHOD_LABELS[method]}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {method === 'contra_entrega'
                          ? 'Paga al recibir tu pedido'
                          : 'Aprobación instantánea simulada'}
                      </p>
                    </button>
                  ))}
                </div>

                <div className="space-y-1.5">
                  <Label>Cupón de descuento (opcional)</Label>
                  <div className="flex gap-2">
                    <Input
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                      placeholder="BOOKLY10"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (!couponCode.trim()) return
                        ordersApi
                          .validateCoupon(couponCode.trim(), subtotal)
                          .then((res) => {
                            setCouponDiscount(Number(res.discount_amount))
                            toast.success(res.message)
                          })
                          .catch((err) => {
                            setCouponDiscount(0)
                            toast.error(extractApiError(err))
                          })
                      }}
                    >
                      Validar
                    </Button>
                  </div>
                </div>

                <div className="flex justify-between pt-3">
                  <Button variant="outline" onClick={() => setStep(3)}>
                    Atrás
                  </Button>
                  <Button size="lg" onClick={handleConfirmOrder} disabled={submitting}>
                    {submitting ? 'Procesando pedido...' : `Confirmar pedido (${formatPEN(estimatedTotal)})`}
                  </Button>
                </div>
              </div>
            )}
          </div>

          <aside className="rounded-2xl border bg-card/60 p-6 space-y-4 h-fit lg:col-span-4">
            <h3 className="font-serif text-lg font-bold">Tu compra ({items.length})</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto text-sm">
              {items.map((item) => (
                <div key={item.id} className="flex justify-between gap-2">
                  <span className="truncate">
                    {item.quantity}x {item.book.title}
                  </span>
                  <span className="shrink-0 font-medium">
                    {formatPEN(Number(item.book.final_price) * item.quantity)}
                  </span>
                </div>
              ))}
            </div>
            <div className="space-y-2 border-t pt-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span>{formatPEN(subtotal)}</span>
              </div>
              {couponDiscount > 0 && (
                <div className="flex justify-between text-emerald-700 dark:text-emerald-400">
                  <span>Descuento</span>
                  <span>-{formatPEN(couponDiscount)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Envío</span>
                <span>{shippingCost === 0 ? 'Gratis' : formatPEN(shippingCost)}</span>
              </div>
              <div className="flex justify-between border-t pt-2 text-base font-bold">
                <span>Total</span>
                <span className="text-primary">{formatPEN(estimatedTotal)}</span>
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}
