import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchUsers } from '../api/users';

const MIN_QUERY_LENGTH = 2;
const DEBOUNCE_MS = 300;

/**
 * Hook para buscar usuarios con debounce. La query solo se dispara cuando
 * `q.trim().length >= MIN_QUERY_LENGTH`, evitando inundar el endpoint mientras
 * el usuario escribe la primera letra.
 */
export function useUserSearch(q: string, limit = 10) {
  const [debouncedQ, setDebouncedQ] = useState(q);

  useEffect(() => {
    const handle = setTimeout(() => setDebouncedQ(q.trim()), DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [q]);

  return useQuery({
    queryKey: ['users', 'search', debouncedQ, limit],
    queryFn: () => searchUsers(debouncedQ, limit),
    enabled: debouncedQ.length >= MIN_QUERY_LENGTH,
    placeholderData: (prev) => prev,
  });
}
