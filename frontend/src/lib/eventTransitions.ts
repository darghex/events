/**
 * Matriz espejo de transiciones (UX-only).
 *
 * El backend (`app/services/event_state.py`) es el source-of-truth de validación.
 * Este archivo solo se usa para renderizar botones contextuales en la UI:
 * dada una tupla `(from, to)` válida, qué label/variante mostrar y si requiere
 * confirmación. Si la matriz del backend cambia, hay que sincronizar aquí.
 */
import type { EventStatus } from '../types/event';

export type ButtonVariant = 'primary' | 'danger';

export interface UITransition {
  to: EventStatus;
  label: string;
  variant: ButtonVariant;
  requiresConfirm: boolean;
}

/**
 * Para cada estado de origen, las transiciones que un owner/admin puede disparar
 * desde la UI. Estados terminales (`FINISHED`, `CANCELLED`) no tienen salidas.
 */
export const UI_TRANSITIONS: Record<EventStatus, UITransition[]> = {
  DRAFT: [
    { to: 'PUBLISHED', label: 'Publicar', variant: 'primary', requiresConfirm: false },
    { to: 'CANCELLED', label: 'Cancelar', variant: 'danger', requiresConfirm: true },
  ],
  PUBLISHED: [
    { to: 'IN_PROGRESS', label: 'Iniciar', variant: 'primary', requiresConfirm: false },
    { to: 'CANCELLED', label: 'Cancelar', variant: 'danger', requiresConfirm: true },
  ],
  IN_PROGRESS: [
    { to: 'FINISHED', label: 'Finalizar', variant: 'primary', requiresConfirm: false },
  ],
  FINISHED: [],
  CANCELLED: [],
};
