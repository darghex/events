import { Link } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { useDeleteSession, useEventSessions } from '../../hooks/sessions';
import type { EventRead } from '../../types/event';
import type { User } from '../../types/auth';
import { Button } from '../ui/Button';

const MUTABLE_STATES = new Set(['DRAFT', 'PUBLISHED']);

interface SessionsAgendaProps {
  event: EventRead;
  user: User | null;
}

function canMutate(event: EventRead, user: User | null): boolean {
  if (!user) return false;
  if (!MUTABLE_STATES.has(event.status)) return false;
  if (user.role === 'ADMIN') return true;
  return user.role === 'ORGANIZER' && user.id === event.owner_id;
}

function formatRange(startIso: string, endIso: string): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const fmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  const timeFmt = new Intl.DateTimeFormat(undefined, { timeStyle: 'short' });
  const sameDay = start.toDateString() === end.toDateString();
  return sameDay ? `${fmt.format(start)} – ${timeFmt.format(end)}` : `${fmt.format(start)} – ${fmt.format(end)}`;
}

export function SessionsAgenda({ event, user }: SessionsAgendaProps) {
  const { data, isLoading, isError } = useEventSessions(event.id);
  const remove = useDeleteSession(event.id);
  const mutable = canMutate(event, user);

  async function onDelete(sessionId: number) {
    if (!confirm('¿Eliminar esta sesión?')) return;
    try {
      await remove.mutateAsync(sessionId);
    } catch (err) {
      alert(extractApiError(err).message);
    }
  }

  return (
    <section style={{ marginTop: '2rem' }} aria-label="Agenda de sesiones">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <h2 style={{ margin: 0 }}>Agenda</h2>
        {mutable && (
          <Link to={`/events/${event.id}/sessions/new`} style={{ color: '#2563eb' }}>
            + Añadir sesión
          </Link>
        )}
      </header>

      {isLoading && <p>Cargando agenda…</p>}
      {isError && <p role="alert">No se pudo cargar la agenda</p>}
      {data && data.length === 0 && (
        <p style={{ color: '#6b7280' }}>Aún no hay sesiones programadas.</p>
      )}

      {data && data.length > 0 && (
        <ul data-testid="sessions-list" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {data.map((s) => (
            <li
              key={s.id}
              style={{
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '0.75rem',
                marginTop: '0.5rem',
                background: '#fff',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <strong>{s.title}</strong>
                {mutable && (
                  <span style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to={`/events/${event.id}/sessions/${s.id}/edit`}>
                      <Button>Editar</Button>
                    </Link>
                    <Button onClick={() => onDelete(s.id)} disabled={remove.isPending}>
                      {remove.isPending ? '…' : 'Eliminar'}
                    </Button>
                  </span>
                )}
              </div>
              <p style={{ margin: '0.25rem 0', color: '#4b5563' }}>
                Ponente: {s.speaker.email}
              </p>
              <p style={{ margin: '0.25rem 0', color: '#4b5563' }}>
                {formatRange(s.start_at, s.end_at)}
              </p>
              {s.capacity != null && (
                <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.875rem' }}>
                  Capacidad: {s.capacity}
                </p>
              )}
              {s.description && (
                <p style={{ margin: '0.5rem 0 0' }}>{s.description}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
