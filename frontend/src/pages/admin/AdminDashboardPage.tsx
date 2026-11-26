import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { AlertTriangle, BookOpen, DollarSign, ShoppingBag, TrendingUp, Users } from 'lucide-react'
import { adminApi } from '@/services/booklyApi'
import { formatPEN } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle, Skeleton } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const CHART_COLORS = ['#243D32', '#C6A66B', '#A8B5A2', '#4D6A5C', '#8F7A52', '#252525']

export function AdminDashboardPage() {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard', startDate, endDate],
    queryFn: () =>
      adminApi.getDashboard({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      }),
  })

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </div>
    )
  }

  const { kpis } = data

  const kpiCards = [
    { label: 'Ingresos totales', value: formatPEN(kpis.total_revenue), icon: DollarSign },
    { label: 'Ventas del día', value: formatPEN(kpis.today_sales), icon: TrendingUp },
    { label: 'Ventas del mes', value: formatPEN(kpis.month_sales), icon: DollarSign },
    { label: 'Ticket promedio', value: formatPEN(kpis.average_ticket), icon: ShoppingBag },
    { label: 'Cantidad de pedidos', value: String(kpis.orders_count), icon: ShoppingBag },
    { label: 'Clientes registrados', value: String(kpis.customers_count), icon: Users },
    { label: 'Libros registrados', value: String(kpis.books_count), icon: BookOpen },
    {
      label: 'Stock bajo / Variación',
      value: `${kpis.low_stock_count} libros • ${kpis.sales_variation_percent}%`,
      icon: AlertTriangle,
    },
  ]

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="font-serif text-3xl font-bold">Dashboard ejecutivo</h1>
          <p className="text-sm text-muted-foreground">
            Indicadores operativos y comerciales en tiempo real desde FastAPI.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-40"
            aria-label="Fecha inicio"
          />
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-40"
            aria-label="Fecha fin"
          />
          {(startDate || endDate) && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setStartDate('')
                setEndDate('')
              }}
            >
              Limpiar
            </Button>
          )}
        </div>
      </div>

      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpiCards.map((card) => {
          const Icon = card.icon
          return (
            <Card key={card.label}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <span className="text-xs font-medium text-muted-foreground">{card.label}</span>
                <Icon className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <p className="font-serif text-2xl font-bold">{card.value}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Gráficos */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Evolución diaria de ventas (S/)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.sales_evolution}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="label" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Area type="monotone" dataKey="value" stroke="#243D32" fill="#A8B5A2" name="S/" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ingresos mensuales (S/)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.monthly_revenue}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="label" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="value" fill="#243D32" radius={[4, 4, 0, 0]} name="Ingresos S/" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ventas por categoría</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.sales_by_category}
                  dataKey="value"
                  nameKey="label"
                  outerRadius={90}
                  label
                >
                  {data.sales_by_category.map((_, idx) => (
                    <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Libros más vendidos (unidades)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_selling_books} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis type="number" fontSize={11} />
                <YAxis type="category" dataKey="label" width={130} fontSize={10} />
                <Tooltip />
                <Bar dataKey="value" fill="#C6A66B" radius={[0, 4, 4, 0]} name="Unidades" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Estados de pedidos</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.orders_by_status}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="label" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" fill="#4D6A5C" radius={[4, 4, 0, 0]} name="Pedidos" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Nuevos clientes registrados</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.new_customers}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="label" fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#C6A66B" strokeWidth={2} name="Clientes" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
