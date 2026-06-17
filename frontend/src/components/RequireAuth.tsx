import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';

export function RequireAuth({ children }: { children: ReactNode }) {
  const { accessToken, refreshToken } = useAuthStore();
  const location = useLocation();

  if (!accessToken && !refreshToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}
