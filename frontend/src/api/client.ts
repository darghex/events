import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../stores/auth';
import type { AccessTokenResponse, ApiError } from '../types/auth';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const api = axios.create({ baseURL: BASE_URL });

// ---- request interceptor: inyecta Authorization si hay access token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- response interceptor: si el access expira, intenta refresh una vez
interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const { data } = await axios.post<AccessTokenResponse>(`${BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    useAuthStore.getState().setAccessToken(data.access_token);
    return data.access_token;
  } catch {
    useAuthStore.getState().logout();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const original = error.config as RetryableConfig | undefined;
    const code = error.response?.data?.error?.code;

    if (!original || original._retried || code !== 'AUTH_TOKEN_EXPIRED') {
      return Promise.reject(error);
    }

    original._retried = true;
    refreshInFlight ??= refreshAccessToken();
    const newToken = await refreshInFlight;
    refreshInFlight = null;

    if (!newToken) {
      return Promise.reject(error);
    }
    original.headers.Authorization = `Bearer ${newToken}`;
    return api.request(original);
  },
);
