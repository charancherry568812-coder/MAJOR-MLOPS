import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  const roleName = typeof user?.role === 'object' ? (user?.role as any)?.name : user?.role
  if (roles && roleName && !roles.includes(roleName)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
