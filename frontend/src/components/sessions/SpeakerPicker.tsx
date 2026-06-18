import { useState } from 'react';
import { useUserSearch } from '../../hooks/users';
import type { UserSearchResult } from '../../types/user';

interface SpeakerPickerProps {
  value: UserSearchResult | null;
  onChange: (speaker: UserSearchResult | null) => void;
}

const MIN_QUERY_LENGTH = 2;

export function SpeakerPicker({ value, onChange }: SpeakerPickerProps) {
  const [q, setQ] = useState('');
  const { data, isFetching } = useUserSearch(q);

  const trimmed = q.trim();
  const showFallback = trimmed.length >= MIN_QUERY_LENGTH && !isFetching && (data ?? []).length === 0;

  return (
    <label style={{ display: 'block', marginBottom: '0.75rem' }}>
      <span style={{ display: 'block', marginBottom: '0.25rem' }}>Ponente</span>
      {value ? (
        <div
          data-testid="speaker-selected"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            background: '#f9fafb',
          }}
        >
          <span style={{ fontWeight: 500 }}>{value.email}</span>
          <button
            type="button"
            onClick={() => {
              onChange(null);
              setQ('');
            }}
            style={{ marginLeft: 'auto', cursor: 'pointer' }}
            aria-label="Quitar ponente seleccionado"
          >
            Cambiar
          </button>
        </div>
      ) : (
        <>
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar por email…"
            aria-label="Buscar ponente"
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              boxSizing: 'border-box',
            }}
          />
          {trimmed.length >= MIN_QUERY_LENGTH && (data ?? []).length > 0 && (
            <ul
              data-testid="speaker-options"
              style={{
                listStyle: 'none',
                margin: '0.25rem 0 0',
                padding: 0,
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                maxHeight: '200px',
                overflowY: 'auto',
              }}
            >
              {data!.map((user) => (
                <li key={user.id}>
                  <button
                    type="button"
                    onClick={() => {
                      onChange(user);
                      setQ('');
                    }}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '0.5rem',
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    {user.email} <small style={{ color: '#6b7280' }}>({user.role})</small>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {showFallback && (
            <p data-testid="speaker-fallback" style={{ color: '#6b7280', fontSize: '0.875rem' }}>
              Si tu ponente no tiene cuenta, pídele que se registre en <code>/register</code>.
            </p>
          )}
        </>
      )}
    </label>
  );
}
