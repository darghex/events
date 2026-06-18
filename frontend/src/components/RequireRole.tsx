import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';
import type { UserRole } from '../types/auth';

interface RequireRoleProps {
  roles: UserRole[];
  children: ReactNode;
}

export function RequireRole({ roles, children }: RequireRoleProps) {
  const { accessToken, refreshToken, user } = useAuthStore();
  const location = useLocation();

  if (!accessToken && !refreshToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (!user) {
    // El perfil aún no se ha hidratado; mostramos placeholder.
    return <p>Cargando…</p>;
  }
  if (!roles.includes(user.role)) {
    return <Navigate to="/events" replace />;
  }
  return <>{children}</>;
}
