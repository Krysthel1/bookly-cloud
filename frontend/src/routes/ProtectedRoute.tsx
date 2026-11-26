import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/useAuthStore'

export function ProtectedRoute({ requireAdmin = false }: { requireAdmin?: boolean }) {
  const { session, profile, isInitialized } = useAuthStore()
  const location = useLocation()

  if (!isInitialized) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-sm text-muted-foreground">
        Verificando sesión...
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/iniciar-sesion" state={{ from: location.pathname }} replace />
  }

  if (requireAdmin && (!profile || !profile.roles.includes('admin'))) {
    return <Navigate to="/no-autorizado" replace />
  }

  return <Outlet />
}
