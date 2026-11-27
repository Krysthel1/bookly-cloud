import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Eye } from 'lucide-react'
import { toast } from 'sonner'
import { adminApi } from '@/services/booklyApi'
import { extractApiError } from '@/lib/api'
import { formatDatePE, formatPEN, ORDER_STATUS_LABELS } from '@/lib/utils'
import type { AdminUser } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'

export function AdminCustomersPage() {
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<string>('')
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null)

  const { data } = useQuery({
    queryKey: ['admin-users', search, activeFilter],
    queryFn: () =>
      adminApi.listUsers({
        search: search || undefined,
        is_active: activeFilter === '' ? undefined : activeFilter === 'true',
      }),
  })

  const { data: userOrders } = useQuery({
    queryKey: ['admin-user-orders', selectedUser?.id],
    queryFn: () => adminApi.getUserOrders(selectedUser!.id),
    enabled: Boolean(selectedUser),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-serif text-3xl font-bold">Clientes registrados</h1>
        <div className="flex flex-wrap gap-2">
          <Input
            placeholder="Buscar por nombre o correo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-60"
          />
          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">Todos los estados</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-card/60 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="p-3">Nombre</th>
              <th className="p-3">Correo</th>
              <th className="p-3">Roles</th>
              <th className="p-3">Pedidos</th>
              <th className="p-3">Total gastado</th>
              <th className="p-3">Registro</th>
              <th className="p-3 text-right">Historial</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(data?.items || []).map((u) => (
              <tr key={u.id}>
                <td className="p-3 font-medium">{u.full_name}</td>
                <td className="p-3">{u.email}</td>
                <td className="p-3 space-x-1">
                  {u.roles.map((r) => (
                    <Badge key={r} variant="outline">
                      {r}
                    </Badge>
                  ))}
                </td>
                <td className="p-3">{u.orders_count}</td>
                <td className="p-3 font-semibold">{formatPEN(u.total_spent)}</td>
                <td className="p-3 text-xs">{formatDatePE(u.created_at)}</td>
                <td className="p-3 text-right">
                  <Button variant="ghost" size="sm" onClick={() => setSelectedUser(u)}>
                    <Eye className="h-4 w-4" />
                    Compras
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={Boolean(selectedUser)} onOpenChange={(open) => !open && setSelectedUser(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Historial de {selectedUser?.full_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm max-h-80 overflow-y-auto">
            {!userOrders || userOrders.items.length === 0 ? (
              <p className="text-muted-foreground">Este cliente aún no registra pedidos.</p>
            ) : (
              userOrders.items.map((o) => (
                <div key={o.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="font-mono font-semibold">{o.order_code}</p>
                    <p className="text-xs text-muted-foreground">{formatDatePE(o.created_at)}</p>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline">{ORDER_STATUS_LABELS[o.status] || o.status}</Badge>
                    <p className="mt-1 font-semibold text-primary">{formatPEN(o.total)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export function AdminCouponsPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    code: '',
    description: '',
    discount_type: 'percentage' as 'percentage' | 'fixed',
    discount_value: '10',
    min_order_amount: '50',
    max_uses: '100',
  })

  const { data: coupons } = useQuery({
    queryKey: ['admin-coupons'],
    queryFn: () => adminApi.listCoupons(),
  })

  const createMutation = useMutation({
    mutationFn: () => {
      const now = new Date()
      const nextMonth = new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000)
      return adminApi.createCoupon({
        code: form.code,
        description: form.description,
        discount_type: form.discount_type,
        discount_value: Number(form.discount_value),
        min_order_amount: Number(form.min_order_amount),
        max_uses: Number(form.max_uses) || undefined,
        starts_at: now.toISOString(),
        expires_at: nextMonth.toISOString(),
        is_active: true,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-coupons'] })
      setForm({ ...form, code: '', description: '' })
      toast.success('Cupón creado')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminApi.updateCoupon(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-coupons'] })
      toast.success('Estado del cupón actualizado')
    },
  })

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl font-bold">Cupones y descuentos</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          createMutation.mutate()
        }}
        className="grid gap-3 rounded-xl border bg-card/40 p-5 sm:grid-cols-3"
      >
        <Input
          required
          placeholder="Código (ej. OTONO15)"
          value={form.code}
          onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
        />
        <select
          value={form.discount_type}
          onChange={(e) =>
            setForm({ ...form, discount_type: e.target.value as 'percentage' | 'fixed' })
          }
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="percentage">Porcentaje (%)</option>
          <option value="fixed">Monto fijo (S/)</option>
        </select>
        <Input
          type="number"
          required
          placeholder="Valor"
          value={form.discount_value}
          onChange={(e) => setForm({ ...form, discount_value: e.target.value })}
        />
        <Input
          type="number"
          placeholder="Compra mínima (S/)"
          value={form.min_order_amount}
          onChange={(e) => setForm({ ...form, min_order_amount: e.target.value })}
        />
        <Input
          type="number"
          placeholder="Límite de usos"
          value={form.max_uses}
          onChange={(e) => setForm({ ...form, max_uses: e.target.value })}
        />
        <Button type="submit">Crear cupón</Button>
      </form>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(coupons || []).map((c) => (
          <div key={c.id} className="rounded-xl border p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-base font-bold">{c.code}</span>
              <Badge variant={c.is_active ? 'gold' : 'destructive'}>
                {c.is_active ? 'Activo' : 'Inactivo'}
              </Badge>
            </div>
            <p className="text-sm">
              {c.discount_type === 'percentage'
                ? `${c.discount_value}% de descuento`
                : `${formatPEN(c.discount_value)} de descuento`}
            </p>
            <p className="text-xs text-muted-foreground">
              Usos: {c.current_uses} / {c.max_uses || '∞'} • Mínimo: {formatPEN(c.min_order_amount)}
            </p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => toggleMutation.mutate({ id: c.id, is_active: !c.is_active })}
            >
              {c.is_active ? 'Desactivar' : 'Activar'}
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}

export function AdminReportsPage() {
  const [selected, setSelected] = useState<'sales' | 'inventory' | 'customers' | 'best-sellers'>('sales')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const params = {
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  }

  const { data } = useQuery({
    queryKey: ['admin-report', selected, startDate, endDate],
    queryFn: () => adminApi.getReport(selected, params),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-serif text-3xl font-bold">Reportes y exportación</h1>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-36"
            aria-label="Fecha inicio reporte"
          />
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-36"
            aria-label="Fecha fin reporte"
          />
          <Button onClick={() => adminApi.downloadReportCsv(selected, params)}>
            <Download className="h-4 w-4" />
            Exportar CSV
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {[
          { id: 'sales' as const, label: 'Ventas e ingresos' },
          { id: 'inventory' as const, label: 'Inventario' },
          { id: 'customers' as const, label: 'Clientes' },
          { id: 'best-sellers' as const, label: 'Más vendidos' },
        ].map((tab) => (
          <Button
            key={tab.id}
            variant={selected === tab.id ? 'default' : 'outline'}
            onClick={() => setSelected(tab.id)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border">
        {data && data.rows.length > 0 ? (
          <table className="w-full text-left text-xs">
            <thead className="border-b bg-card/60 uppercase text-muted-foreground">
              <tr>
                {Object.keys(data.rows[0]).map((col) => (
                  <th key={col} className="p-3">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.rows.slice(0, 50).map((row, idx) => (
                <tr key={idx}>
                  {Object.values(row).map((val, cIdx) => (
                    <td key={cIdx} className="p-3">
                      {String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="p-6 text-sm text-muted-foreground">Sin registros para este reporte.</p>
        )}
      </div>
    </div>
  )
}

export function AdminAuditPage() {
  const { data } = useQuery({
    queryKey: ['admin-audit'],
    queryFn: () => adminApi.listAuditLogs(1),
  })

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl font-bold">Registros de auditoría</h1>
      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-left text-xs">
          <thead className="border-b bg-card/60 uppercase text-muted-foreground">
            <tr>
              <th className="p-3">Fecha</th>
              <th className="p-3">Actor</th>
              <th className="p-3">Acción</th>
              <th className="p-3">Entidad</th>
              <th className="p-3">Detalle</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(data?.items || []).map((log) => (
              <tr key={log.id}>
                <td className="p-3">{formatDatePE(log.created_at)}</td>
                <td className="p-3">{log.actor_email || 'Sistema'}</td>
                <td className="p-3 font-mono font-semibold">{log.action}</td>
                <td className="p-3">
                  {log.entity_type} ({log.entity_id.slice(0, 8)})
                </td>
                <td className="p-3 font-mono text-[11px]">
                  {JSON.stringify(log.new_values || log.old_values || {})}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
