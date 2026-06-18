import type { AxiosError } from 'axios';
import type { ApiError } from '../types/auth';

const MESSAGES: Record<string, string> = {
  AUTH_INVALID_CREDENTIALS: 'Email o contraseña incorrectos',
  AUTH_TOKEN_EXPIRED: 'Tu sesión expiró, vuelve a ingresar',
  FORBIDDEN: 'No tienes permisos para esta acción',
  NOT_FOUND: 'Recurso no encontrado',
  VALIDATION_ERROR: 'Datos inválidos',
  USER_ALREADY_EXISTS: 'Este email ya está registrado',
  EVENT_NOT_MUTABLE: 'El evento solo puede modificarse mientras está en Borrador',
};

export function extractApiError(err: unknown): { code?: string; message: string } {
  const axiosErr = err as AxiosError<ApiError>;
  const apiError = axiosErr.response?.data?.error;
  if (apiError) {
    const code = apiError.code;
    return {
      code,
      message: MESSAGES[code] ?? apiError.message ?? 'Error inesperado',
    };
  }
  return { message: 'Error de red, intenta de nuevo' };
}
