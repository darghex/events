import { Link } from 'react-router-dom';
import { StatusBadge } from '../ui/Badge';
import type { EventListItem } from '../../types/event';

function formatRange(startIso: string, endIso: string): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const fmt = new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
  const sameDay = start.toDateString() === end.toDateString();
  if (sameDay) {
    const timeFmt = new Intl.DateTimeFormat(undefined, { timeStyle: 'short' });
    return `${fmt.format(start)} – ${timeFmt.format(end)}`;
  }
  return `${fmt.format(start)} – ${fmt.format(end)}`;
}

export function EventoCard({ event }: { event: EventListItem }) {
  return (
    <article
      data-testid="evento-card"
      style={{
        border: '1px solid #d1d5db',
        borderRadius: '8px',
        padding: '1rem',
        marginBottom: '0.75rem',
        background: '#fff',
      }}
    >
      <header
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}
      >
        <h3 style={{ margin: 0 }}>
          <Link to={`/events/${event.id}`} style={{ color: '#111', textDecoration: 'none' }}>
            {event.title}
          </Link>
        </h3>
        <StatusBadge status={event.status} />
      </header>
      <p style={{ margin: '0.25rem 0', color: '#4b5563' }}>{event.location}</p>
      <p style={{ margin: '0.25rem 0', color: '#4b5563' }}>{formatRange(event.start_at, event.end_at)}</p>
      <p style={{ margin: '0.25rem 0', color: '#6b7280', fontSize: '0.875rem' }}>
        Capacidad: {event.capacity}
      </p>
    </article>
  );
}
