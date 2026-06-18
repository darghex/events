import { useState } from 'react';
import { Link } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { useCancelMyRegistration, useRegisterForEvent } from '../../hooks/registrations';
import type { EventRead } from '../../types/event';
import type { User } from '../../types/auth';
import { Button } from '../ui/Button';

interface RegistrationButtonProps {
  event: EventRead;
  user: User | null;
}

export function RegistrationButton({ event, user }: RegistrationButtonProps) {
  const register = useRegisterForEvent(event.id);
  const cancel = useCancelMyRegistration(event.id);
  const [error, setError] = useState<string | null>(null);

  const counter = `${event.confirmed_count} / ${event.capacity}`;

  if (!user) {
    return (
      <div data-testid="registration-cta" style={containerStyle}>
        <span style={counterStyle}>{counter}</span>
        <Link to="/login" style={{ color: '#2563eb' }}>
          Inicia sesión para inscribirte
        </Link>
      </div>
    );
  }

  if (event.status !== 'PUBLISHED') {
    return (
      <div data-testid="registration-cta" style={containerStyle}>
        <span style={counterStyle}>{counter}</span>
        <span style={{ color: '#6b7280' }}>Inscripciones no disponibles en este estado</span>
      </div>
    );
  }

  async function onRegister() {
    setError(null);
    try {
      await register.mutateAsync();
    } catch (err) {
      setError(extractApiError(err).message);
    }
  }

  async function onCancel() {
    if (!confirm('¿Cancelar tu inscripción a este evento?')) return;
    setError(null);
    try {
      await cancel.mutateAsync();
    } catch (err) {
      setError(extractApiError(err).message);
    }
  }

  return (
    <div data-testid="registration-cta" style={containerStyle}>
      <span style={counterStyle}>{counter}</span>
      {event.my_registration_status === 'CONFIRMED' ? (
        <Button
          onClick={onCancel}
          disabled={cancel.isPending}
          style={{ background: '#b91c1c', border: '1px solid #7f1d1d' }}
        >
          {cancel.isPending ? '…' : 'Cancelar mi inscripción'}
        </Button>
      ) : event.is_full ? (
        <Button disabled aria-label="Cupo lleno">
          Cupo lleno
        </Button>
      ) : (
        <Button onClick={onRegister} disabled={register.isPending}>
          {register.isPending ? '…' : 'Inscribirme'}
        </Button>
      )}
      {error && (
        <p role="alert" style={{ color: '#c00', margin: 0 }}>
          {error}
        </p>
      )}
    </div>
  );
}

const containerStyle: React.CSSProperties = {
  display: 'flex',
  gap: '0.75rem',
  alignItems: 'center',
  marginTop: '0.5rem',
  flexWrap: 'wrap',
};

const counterStyle: React.CSSProperties = {
  fontSize: '0.875rem',
  color: '#4b5563',
};
