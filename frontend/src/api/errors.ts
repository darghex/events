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
  INVALID_TRANSITION: 'Esta transición no está permitida en el estado actual',
  SESSION_OUT_OF_RANGE: 'La sesión debe caer dentro del marco temporal del evento',
  SESSION_OVERLAP: 'El ponente ya tiene una sesión que se solapa en ese horario',
  SESSION_CAPACITY_EXCEEDS_EVENT: 'La capacidad de la sesión no puede superar la del evento',
  EVENT_CAPACITY_BELOW_SESSION:
    'No puedes reducir el aforo del evento por debajo de una sesión existente',
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
