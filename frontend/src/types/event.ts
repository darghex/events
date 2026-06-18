export type EventStatus = 'DRAFT' | 'PUBLISHED' | 'IN_PROGRESS' | 'FINISHED' | 'CANCELLED';

export type RegistrationStatus = 'CONFIRMED' | 'CANCELLED';

export interface EventRead {
  id: number;
  title: string;
  description: string | null;
  location: string;
  capacity: number;
  start_at: string;
  end_at: string;
  status: EventStatus;
  owner_id: number;
  created_at: string;
  updated_at: string;
  confirmed_count: number;
  is_full: boolean;
  my_registration_status: RegistrationStatus | null;
}

export interface EventListItem {
  id: number;
  title: string;
  location: string;
  start_at: string;
  end_at: string;
  capacity: number;
  status: EventStatus;
  owner_id: number;
  confirmed_count: number;
  is_full: boolean;
}

export interface EventsPage {
  items: EventListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface EventCreateInput {
  title: string;
  description?: string | null;
  location: string;
  capacity: number;
  start_at: string;
  end_at: string;
}

export type EventUpdateInput = Partial<EventCreateInput>;

export interface EventsListParams {
  q?: string;
  limit?: number;
  offset?: number;
}
