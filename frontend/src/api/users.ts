import { api } from './client';
import type { UserSearchResult } from '../types/user';

export async function searchUsers(q: string, limit = 10): Promise<UserSearchResult[]> {
  const { data } = await api.get<UserSearchResult[]>('/users', {
    params: { q: q || undefined, limit },
  });
  return data;
}
