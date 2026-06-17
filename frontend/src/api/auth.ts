import { api } from './client';
import type { TokenPair, User } from '../types/auth';

export async function registerUser(email: string, password: string): Promise<User> {
  const { data } = await api.post<User>('/auth/register', { email, password });
  return data;
}

export async function login(email: string, password: string): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>('/auth/login', { email, password });
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}
