import { api } from './client';
import type {
  RegistrationRead,
  RegistrationsPage,
} from '../types/registration';

export async function registerForEvent(eventId: number): Promise<RegistrationRead> {
  const { data } = await api.post<RegistrationRead>(`/events/${eventId}/registrations`);
  return data;
}

export async function cancelMyRegistration(eventId: number): Promise<void> {
  await api.delete(`/events/${eventId}/registrations/me`);
}

export async function listMyRegistrations(params: {
  limit?: number;
  offset?: number;
} = {}): Promise<RegistrationsPage> {
  const { data } = await api.get<RegistrationsPage>('/me/registrations', { params });
  return data;
}
