import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { useAuthStore } from '@/stores/useAuthStore'
import { useCartStore } from '@/stores/useCartStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { PublicLayout } from '@/layouts/PublicLayout'
import { AdminLayout } from '@/layouts/AdminLayout'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { HomePage } from '@/pages/HomePage'
import { CatalogPage } from '@/pages/CatalogPage'
import { BookDetailPage } from '@/pages/BookDetailPage'
import { CartPage } from '@/pages/CartPage'
import { CheckoutPage } from '@/pages/CheckoutPage'
import {
  EmailConfirmationPage,
  ForgotPasswordPage,
  LoginPage,
  RegisterPage,
  ResetPasswordPage,
} from '@/pages/AuthPages'
import {
  AccountAddressesPage,
  AccountFavoritesPage,
  AccountLayout,
  AccountNotificationsPage,
  AccountOrderDetailPage,
  AccountOrdersPage,
  AccountProfilePage,
  AccountSettingsPage,
} from '@/pages/AccountPages'
import {
  AboutPage,
  ContactPage,
  FaqPage,
  NotFoundPage,
  PrivacyPage,
  TermsPage,
  UnauthorizedPage,
} from '@/pages/StaticPages'
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage'
import { AdminBooksPage } from '@/pages/admin/AdminBooksPage'
import {
  AdminAuthorsPage,
  AdminCategoriesPage,
  AdminInventoryPage,
  AdminOrdersPage,
} from '@/pages/admin/AdminOperationsPages'
import {
  AdminAuditPage,
  AdminCouponsPage,
  AdminCustomersPage,
  AdminReportsPage,
} from '@/pages/admin/AdminManagementPages'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function AppBootstrap({ children }: { children: React.ReactNode }) {
  const initializeAuth = useAuthStore((s) => s.initialize)
  const session = useAuthStore((s) => s.session)
  const fetchCart = useCartStore((s) => s.fetchCart)
  const initTheme = useThemeStore((s) => s.initTheme)

  useEffect(() => {
    initTheme()
    initializeAuth()
  }, [initTheme, initializeAuth])

  useEffect(() => {
    fetchCart()
  }, [session, fetchCart])

  return <>{children}</>
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppBootstrap>
          <Routes>
            <Route element={<PublicLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/catalogo" element={<CatalogPage />} />
              <Route path="/libros/:id" element={<BookDetailPage />} />
              <Route path="/carrito" element={<CartPage />} />
              <Route path="/iniciar-sesion" element={<LoginPage />} />
              <Route path="/registro" element={<RegisterPage />} />
              <Route path="/confirmacion-correo" element={<EmailConfirmationPage />} />
              <Route path="/recuperar-contrasena" element={<ForgotPasswordPage />} />
              <Route path="/restablecer-contrasena" element={<ResetPasswordPage />} />
              <Route path="/nosotros" element={<AboutPage />} />
              <Route path="/contacto" element={<ContactPage />} />
              <Route path="/preguntas-frecuentes" element={<FaqPage />} />
              <Route path="/privacidad" element={<PrivacyPage />} />
              <Route path="/terminos" element={<TermsPage />} />
              <Route path="/no-autorizado" element={<UnauthorizedPage />} />

              <Route element={<ProtectedRoute />}>
                <Route path="/checkout" element={<CheckoutPage />} />
                <Route path="/mi-cuenta" element={<AccountLayout />}>
                  <Route index element={<AccountProfilePage />} />
                  <Route path="pedidos" element={<AccountOrdersPage />} />
                  <Route path="pedidos/:orderId" element={<AccountOrderDetailPage />} />
                  <Route path="direcciones" element={<AccountAddressesPage />} />
                  <Route path="favoritos" element={<AccountFavoritesPage />} />
                  <Route path="notificaciones" element={<AccountNotificationsPage />} />
                  <Route path="configuracion" element={<AccountSettingsPage />} />
                </Route>
              </Route>

              <Route path="*" element={<NotFoundPage />} />
            </Route>

            <Route element={<ProtectedRoute requireAdmin />}>
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<AdminDashboardPage />} />
                <Route path="libros" element={<AdminBooksPage />} />
                <Route path="categorias" element={<AdminCategoriesPage />} />
                <Route path="autores" element={<AdminAuthorsPage />} />
                <Route path="inventario" element={<AdminInventoryPage />} />
                <Route path="pedidos" element={<AdminOrdersPage />} />
                <Route path="clientes" element={<AdminCustomersPage />} />
                <Route path="descuentos" element={<AdminCouponsPage />} />
                <Route path="reportes" element={<AdminReportsPage />} />
                <Route path="auditoria" element={<AdminAuditPage />} />
              </Route>
            </Route>
          </Routes>
          <Toaster richColors position="top-right" />
        </AppBootstrap>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
