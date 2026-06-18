import { api } from './client';
import type {
  SessionCreateInput,
  SessionRead,
  SessionUpdateInput,
} from '../types/session';

export async function listSessions(eventId: number): Promise<SessionRead[]> {
  const { data } = await api.get<SessionRead[]>(`/events/${eventId}/sessions`);
  return data;
}

export async function getSession(eventId: number, sessionId: number): Promise<SessionRead> {
  const { data } = await api.get<SessionRead>(`/events/${eventId}/sessions/${sessionId}`);
  return data;
}

export async function createSession(
  eventId: number,
  input: SessionCreateInput,
): Promise<SessionRead> {
  const { data } = await api.post<SessionRead>(`/events/${eventId}/sessions`, input);
  return data;
}

export async function updateSession(
  eventId: number,
  sessionId: number,
  patch: SessionUpdateInput,
): Promise<SessionRead> {
  const { data } = await api.patch<SessionRead>(
    `/events/${eventId}/sessions/${sessionId}`,
    patch,
  );
  return data;
}

export async function deleteSession(eventId: number, sessionId: number): Promise<void> {
  await api.delete(`/events/${eventId}/sessions/${sessionId}`);
}
