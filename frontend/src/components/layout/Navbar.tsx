import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  BookMarked,
  Heart,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  ShoppingBag,
  Sun,
  User,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/stores/useAuthStore'
import { useCartStore } from '@/stores/useCartStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function Navbar() {
  const [searchTerm, setSearchTerm] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const navigate = useNavigate()

  const { profile, session, signOut, isAdmin } = useAuthStore()
  const itemsCount = useCartStore((s) => s.itemsCount)
  const { theme, toggleTheme } = useThemeStore()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const q = searchTerm.trim()
    navigate(q ? `/catalogo?search=${encodeURIComponent(q)}` : '/catalogo')
    setMobileMenuOpen(false)
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur-md">
      <div className="container flex h-16 items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-bookly-forest text-bookly-gold">
              <BookMarked className="h-5 w-5" />
            </div>
            <span className="font-serif text-xl font-bold tracking-wider text-primary">BOOKLY</span>
          </Link>

          <nav className="hidden items-center gap-5 text-sm font-medium md:flex">
            <Link to="/catalogo" className="text-muted-foreground transition hover:text-primary">
              Catálogo
            </Link>
            <Link
              to="/catalogo?on_sale=true"
              className="text-muted-foreground transition hover:text-primary"
            >
              Ofertas
            </Link>
            <Link to="/nosotros" className="text-muted-foreground transition hover:text-primary">
              Nosotros
            </Link>
            <Link to="/contacto" className="text-muted-foreground transition hover:text-primary">
              Contacto
            </Link>
          </nav>
        </div>

        <form onSubmit={handleSearch} className="hidden max-w-sm flex-1 lg:flex">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar título, autor o ISBN..."
              className="pl-9 pr-4 bg-card/50"
              aria-label="Buscar libros"
            />
          </div>
        </form>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Cambiar tema claro u oscuro"
          >
            {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>

          <Button variant="ghost" size="icon" asChild aria-label="Favoritos">
            <Link to="/mi-cuenta/favoritos">
              <Heart className="h-4 w-4" />
            </Link>
          </Button>

          <Button variant="ghost" size="icon" className="relative" asChild aria-label="Carrito de compras">
            <Link to="/carrito">
              <ShoppingBag className="h-4 w-4" />
              {itemsCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-bookly-gold px-1 text-[10px] font-bold text-bookly-charcoal">
                  {itemsCount}
                </span>
              )}
            </Link>
          </Button>

          {session && profile ? (
            <div className="hidden items-center gap-2 sm:flex">
              {isAdmin() && (
                <Button variant="outline" size="sm" asChild>
                  <Link to="/admin">
                    <LayoutDashboard className="h-4 w-4" />
                    Admin
                  </Link>
                </Button>
              )}
              <Button variant="ghost" size="sm" asChild>
                <Link to="/mi-cuenta">
                  <User className="h-4 w-4" />
                  <span className="max-w-[110px] truncate">{profile.full_name}</span>
                </Link>
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => signOut()}
                aria-label="Cerrar sesión"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <div className="hidden items-center gap-2 sm:flex">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/iniciar-sesion">Ingresar</Link>
              </Button>
              <Button size="sm" asChild>
                <Link to="/registro">Crear cuenta</Link>
              </Button>
            </div>
          )}

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen((v) => !v)}
            aria-label="Menú móvil"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="border-t bg-background p-4 md:hidden">
          <form onSubmit={handleSearch} className="mb-4 flex gap-2">
            <Input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar libros..."
            />
            <Button type="submit" size="sm">
              Buscar
            </Button>
          </form>
          <div className="flex flex-col space-y-2 text-sm">
            <Link to="/catalogo" onClick={() => setMobileMenuOpen(false)} className="py-1.5">
              Catálogo completo
            </Link>
            <Link to="/catalogo?on_sale=true" onClick={() => setMobileMenuOpen(false)} className="py-1.5">
              Ofertas especiales
            </Link>
            <Link to="/nosotros" onClick={() => setMobileMenuOpen(false)} className="py-1.5">
              Nosotros
            </Link>
            <Link to="/contacto" onClick={() => setMobileMenuOpen(false)} className="py-1.5">
              Contacto
            </Link>
            {session ? (
              <>
                <Link to="/mi-cuenta" onClick={() => setMobileMenuOpen(false)} className="py-1.5 font-medium">
                  Mi cuenta
                </Link>
                {isAdmin() && (
                  <Link to="/admin" onClick={() => setMobileMenuOpen(false)} className="py-1.5 font-medium text-primary">
                    Panel Administrativo
                  </Link>
                )}
                <Button variant="outline" size="sm" onClick={() => signOut()}>
                  Cerrar sesión
                </Button>
              </>
            ) : (
              <div className="flex gap-2 pt-2">
                <Button variant="outline" className="flex-1" asChild>
                  <Link to="/iniciar-sesion" onClick={() => setMobileMenuOpen(false)}>
                    Ingresar
                  </Link>
                </Button>
                <Button className="flex-1" asChild>
                  <Link to="/registro" onClick={() => setMobileMenuOpen(false)}>
                    Registrarse
                  </Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
