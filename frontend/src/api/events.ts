import { api } from './client';
import type {
  EventCreateInput,
  EventRead,
  EventUpdateInput,
  EventsListParams,
  EventsPage,
} from '../types/event';

export async function listEvents(params: EventsListParams = {}): Promise<EventsPage> {
  const { data } = await api.get<EventsPage>('/events', { params });
  return data;
}

export async function listMyEvents(
  params: Omit<EventsListParams, 'q'> = {},
): Promise<EventsPage> {
  const { data } = await api.get<EventsPage>('/events/me', { params });
  return data;
}

export async function getEvent(id: number): Promise<EventRead> {
  const { data } = await api.get<EventRead>(`/events/${id}`);
  return data;
}

export async function createEvent(input: EventCreateInput): Promise<EventRead> {
  const { data } = await api.post<EventRead>('/events', input);
  return data;
}

export async function updateEvent(id: number, patch: EventUpdateInput): Promise<EventRead> {
  const { data } = await api.patch<EventRead>(`/events/${id}`, patch);
  return data;
}

export async function deleteEvent(id: number): Promise<void> {
  await api.delete(`/events/${id}`);
}
