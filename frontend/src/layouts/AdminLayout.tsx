import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  BarChart3,
  BookMarked,
  BookOpen,
  Boxes,
  FileSpreadsheet,
  FolderTree,
  LayoutDashboard,
  Menu,
  Moon,
  ShieldCheck,
  ShoppingCart,
  Sun,
  Tag,
  Users,
  UserPen,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/stores/useAuthStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { Button } from '@/components/ui/button'

const ADMIN_NAV = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/libros', label: 'Libros', icon: BookOpen },
  { to: '/admin/categorias', label: 'Categorías', icon: FolderTree },
  { to: '/admin/autores', label: 'Autores', icon: UserPen },
  { to: '/admin/inventario', label: 'Inventario', icon: Boxes },
  { to: '/admin/pedidos', label: 'Pedidos', icon: ShoppingCart },
  { to: '/admin/clientes', label: 'Clientes', icon: Users },
  { to: '/admin/descuentos', label: 'Cupones', icon: Tag },
  { to: '/admin/reportes', label: 'Reportes', icon: FileSpreadsheet },
  { to: '/admin/auditoria', label: 'Auditoría', icon: ShieldCheck },
]

export function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const profile = useAuthStore((s) => s.profile)
  const { theme, toggleTheme } = useThemeStore()

  const activeNav = ADMIN_NAV.find((item) =>
    item.end ? location.pathname === item.to : location.pathname.startsWith(item.to),
  )

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar escritorio */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 border-r bg-bookly-forest text-bookly-cream transition-transform lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-white/10 px-5">
          <Link to="/admin" className="flex items-center gap-2.5">
            <BookMarked className="h-5 w-5 text-bookly-gold" />
            <span className="font-serif text-lg font-bold tracking-wider">BOOKLY ADMIN</span>
          </Link>
          <button
            type="button"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Cerrar menú"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="space-y-1 p-3">
          {ADMIN_NAV.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? 'bg-bookly-gold text-bookly-charcoal'
                      : 'text-bookly-cream/80 hover:bg-white/10 hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="mt-auto border-t border-white/10 p-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-xs text-bookly-sage hover:text-bookly-gold"
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Volver a la tienda pública →
          </Link>
        </div>
      </aside>

      <div className="flex flex-1 flex-col min-w-0">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-6 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="text-xs text-muted-foreground">
              <span>Admin</span> /{' '}
              <span className="font-semibold text-foreground">{activeNav?.label || 'Panel'}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Tema">
              {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </Button>
            <span className="hidden text-sm font-medium sm:inline">{profile?.full_name}</span>
          </div>
        </header>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
