import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMyRegistrations } from '../../hooks/registrations';
import { Pagination } from '../../components/ui/Pagination';
import { StatusBadge } from '../../components/ui/Badge';
import type { RegistrationStatus } from '../../types/registration';

const PAGE_SIZE = 20;

function statusLabel(status: RegistrationStatus): { label: string; bg: string; fg: string } {
  return status === 'CONFIRMED'
    ? { label: 'Confirmada', bg: '#dcfce7', fg: '#166534' }
    : { label: 'Cancelada', bg: '#fee2e2', fg: '#991b1b' };
}

function formatRange(startIso: string, endIso: string): string {
  const fmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  return `${fmt.format(new Date(startIso))} – ${fmt.format(new Date(endIso))}`;
}

export default function MyRegistrationsPage() {
  const [offset, setOffset] = useState(0);
  const { data, isLoading, isError } = useMyRegistrations({ limit: PAGE_SIZE, offset });

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>Mis inscripciones</h1>

      {isLoading && <p>Cargando…</p>}
      {isError && <p role="alert">No se pudo cargar tu historial</p>}
      {data && data.items.length === 0 && (
        <p style={{ color: '#6b7280' }}>
          Aún no te has inscrito a ningún evento. Explora la <Link to="/events">cartelera</Link>.
        </p>
      )}

      {data && data.items.length > 0 && (
        <ul data-testid="my-registrations" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {data.items.map((reg) => {
            const { label, bg, fg } = statusLabel(reg.status);
            return (
              <li
                key={reg.id}
                style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  marginTop: '0.5rem',
                  background: '#fff',
                }}
              >
                <header
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                  }}
                >
                  <h3 style={{ margin: 0 }}>
                    <Link to={`/events/${reg.event.id}`} style={{ color: '#111', textDecoration: 'none' }}>
                      {reg.event.title}
                    </Link>
                  </h3>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '0.125rem 0.5rem',
                      borderRadius: '999px',
                      background: bg,
                      color: fg,
                      fontSize: '0.75rem',
                      fontWeight: 600,
                    }}
                  >
                    {label}
                  </span>
                </header>
                <p style={{ margin: '0.25rem 0', color: '#4b5563' }}>{reg.event.location}</p>
                <p style={{ margin: '0.25rem 0', color: '#4b5563' }}>
                  {formatRange(reg.event.start_at, reg.event.end_at)}
                </p>
                <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.875rem' }}>
                  Estado del evento: <StatusBadge status={reg.event.status} />
                </p>
              </li>
            );
          })}
        </ul>
      )}

      {data && data.total > PAGE_SIZE && (
        <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
      )}
    </main>
  );
}
