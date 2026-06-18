import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createEvent,
  deleteEvent,
  getEvent,
  listEvents,
  listMyEvents,
  updateEvent,
} from '../api/events';
import type {
  EventCreateInput,
  EventUpdateInput,
  EventsListParams,
} from '../types/event';

const EVENTS_KEY = 'events';

export function useEventsList(params: EventsListParams) {
  return useQuery({
    queryKey: [EVENTS_KEY, 'list', params],
    queryFn: () => listEvents(params),
    placeholderData: (prev) => prev,
  });
}

export function useMyEvents(params: Omit<EventsListParams, 'q'>) {
  return useQuery({
    queryKey: [EVENTS_KEY, 'me', params],
    queryFn: () => listMyEvents(params),
    placeholderData: (prev) => prev,
  });
}

export function useEventDetail(id: number | undefined) {
  return useQuery({
    queryKey: [EVENTS_KEY, 'detail', id],
    queryFn: () => getEvent(id as number),
    enabled: typeof id === 'number' && !Number.isNaN(id),
  });
}

function useInvalidateLists() {
  const qc = useQueryClient();
  // Invalida todo el sub-árbol ["events", ...]: list, me y detail.
  return () => qc.invalidateQueries({ queryKey: [EVENTS_KEY] });
}

export function useCreateEvent() {
  const invalidate = useInvalidateLists();
  return useMutation({
    mutationFn: (input: EventCreateInput) => createEvent(input),
    onSuccess: invalidate,
  });
}

export function useUpdateEvent(id: number) {
  const invalidate = useInvalidateLists();
  return useMutation({
    mutationFn: (patch: EventUpdateInput) => updateEvent(id, patch),
    onSuccess: invalidate,
  });
}

export function useDeleteEvent() {
  const invalidate = useInvalidateLists();
  return useMutation({
    mutationFn: (id: number) => deleteEvent(id),
    onSuccess: invalidate,
  });
}
