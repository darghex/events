import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  cancelMyRegistration,
  listMyRegistrations,
  registerForEvent,
} from '../api/registrations';

const EVENTS_KEY = 'events';
const ME_REGISTRATIONS_KEY = 'me-registrations';

function useInvalidateAll() {
  const qc = useQueryClient();
  // Invalidar todo el sub-árbol de eventos (incluye conteos, my_registration_status,
  // detalle y listas) más el historial /me/registrations.
  return () => {
    qc.invalidateQueries({ queryKey: [EVENTS_KEY] });
    qc.invalidateQueries({ queryKey: [ME_REGISTRATIONS_KEY] });
  };
}

export function useRegisterForEvent(eventId: number) {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: () => registerForEvent(eventId),
    onSuccess: invalidate,
  });
}

export function useCancelMyRegistration(eventId: number) {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: () => cancelMyRegistration(eventId),
    onSuccess: invalidate,
  });
}

export function useMyRegistrations(params: { limit?: number; offset?: number } = {}) {
  return useQuery({
    queryKey: [ME_REGISTRATIONS_KEY, params],
    queryFn: () => listMyRegistrations(params),
    placeholderData: (prev) => prev,
  });
}
