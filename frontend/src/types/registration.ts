import type { EventListItem } from './event';

export type RegistrationStatus = 'CONFIRMED' | 'CANCELLED';

export interface RegistrationRead {
  id: number;
  user_id: number;
  event_id: number;
  status: RegistrationStatus;
  created_at: string;
  updated_at: string;
}

export interface RegistrationWithEvent extends RegistrationRead {
  event: EventListItem;
}

export interface RegistrationsPage {
  items: RegistrationWithEvent[];
  total: number;
  limit: number;
  offset: number;
}
