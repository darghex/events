import type { UserRole } from './auth';

export interface UserSearchResult {
  id: number;
  email: string;
  role: UserRole;
}
