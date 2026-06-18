import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createSession,
  deleteSession,
  getSession,
  listSessions,
  updateSession,
} from '../api/sessions';
import type { SessionCreateInput, SessionUpdateInput } from '../types/session';

const EVENTS_KEY = 'events';

function sessionsKey(eventId: number) {
  return [EVENTS_KEY, eventId, 'sessions'] as const;
}

export function useEventSessions(eventId: number | undefined) {
  return useQuery({
    queryKey: typeof eventId === 'number' ? sessionsKey(eventId) : [EVENTS_KEY, 'sessions', 'idle'],
    queryFn: () => listSessions(eventId as number),
    enabled: typeof eventId === 'number' && !Number.isNaN(eventId),
  });
}

export function useSession(eventId: number | undefined, sessionId: number | undefined) {
  return useQuery({
    queryKey:
      typeof eventId === 'number' && typeof sessionId === 'number'
        ? [EVENTS_KEY, eventId, 'sessions', sessionId]
        : [EVENTS_KEY, 'sessions', 'idle'],
    queryFn: () => getSession(eventId as number, sessionId as number),
    enabled: typeof eventId === 'number' && typeof sessionId === 'number',
  });
}

function useInvalidateEvent(eventId: number) {
  const qc = useQueryClient();
  // Invalida toda la sub-rama del evento (sesiones, detalle y listas).
  return () => qc.invalidateQueries({ queryKey: [EVENTS_KEY] });
}

export function useCreateSession(eventId: number) {
  const invalidate = useInvalidateEvent(eventId);
  return useMutation({
    mutationFn: (input: SessionCreateInput) => createSession(eventId, input),
    onSuccess: invalidate,
  });
}

export function useUpdateSession(eventId: number, sessionId: number) {
  const invalidate = useInvalidateEvent(eventId);
  return useMutation({
    mutationFn: (patch: SessionUpdateInput) => updateSession(eventId, sessionId, patch),
    onSuccess: invalidate,
  });
}

export function useDeleteSession(eventId: number) {
  const invalidate = useInvalidateEvent(eventId);
  return useMutation({
    mutationFn: (sessionId: number) => deleteSession(eventId, sessionId),
    onSuccess: invalidate,
  });
}
