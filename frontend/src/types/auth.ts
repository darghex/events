export type UserRole = 'ADMIN' | 'ORGANIZER' | 'ATTENDEE';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: 'bearer';
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
