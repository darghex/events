export interface Speaker {
  id: number;
  email: string;
}

export interface SessionRead {
  id: number;
  event_id: number;
  speaker_id: number;
  title: string;
  description: string | null;
  start_at: string;
  end_at: string;
  capacity: number | null;
  created_at: string;
  updated_at: string;
  speaker: Speaker;
}

export interface SessionCreateInput {
  title: string;
  description?: string | null;
  speaker_id: number;
  start_at: string;
  end_at: string;
  capacity?: number | null;
}

export type SessionUpdateInput = Partial<SessionCreateInput>;
