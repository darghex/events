import { useState } from 'react';
import { extractApiError } from '../../api/errors';
import { useTransitionEvent } from '../../hooks/events';
import { UI_TRANSITIONS } from '../../lib/eventTransitions';
import type { EventRead, EventStatus } from '../../types/event';
import type { User } from '../../types/auth';
import { Button } from '../ui/Button';

interface EventTransitionsBarProps {
  event: EventRead;
  user: User | null;
}

function canActOn(event: EventRead, user: User | null): boolean {
  if (!user) return false;
  if (user.role === 'ADMIN') return true;
  return user.role === 'ORGANIZER' && user.id === event.owner_id;
}

export function EventTransitionsBar({ event, user }: EventTransitionsBarProps) {
  const transitions = UI_TRANSITIONS[event.status];
  const transition = useTransitionEvent(event.id);
  const [error, setError] = useState<string | null>(null);

  if (!canActOn(event, user)) return null;
  if (transitions.length === 0) return null;

  async function handleClick(to: EventStatus, requiresConfirm: boolean) {
    if (requiresConfirm && !confirm('¿Confirmar esta acción? No se puede deshacer.')) return;
    setError(null);
    try {
      await transition.mutateAsync(to);
    } catch (err) {
      setError(extractApiError(err).message);
    }
  }

  return (
    <div
      data-testid="event-transitions-bar"
      style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '1rem', flexWrap: 'wrap' }}
    >
      {transitions.map((t) => (
        <Button
          key={t.to}
          onClick={() => handleClick(t.to, t.requiresConfirm)}
          disabled={transition.isPending}
          style={t.variant === 'danger' ? { background: '#b91c1c', border: '1px solid #7f1d1d' } : undefined}
          aria-label={t.label}
        >
          {transition.isPending ? '…' : t.label}
        </Button>
      ))}
      {error && (
        <p role="alert" style={{ color: '#c00', margin: 0 }}>
          {error}
        </p>
      )}
    </div>
  );
}
