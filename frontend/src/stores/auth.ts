import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { TokenPair, User } from '../types/auth';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  setSession: (tokens: TokenPair) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

// Refresh token persistido en localStorage como fallback documentado.
// Migración futura: mover a cookie httpOnly cuando el backend lo soporte.
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: (tokens) =>
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),
      setAccessToken: (token) => set({ accessToken: token }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: 'mis-eventos-auth',
      partialize: (state) => ({ refreshToken: state.refreshToken }),
    },
  ),
);
