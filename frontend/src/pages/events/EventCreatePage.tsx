import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { EventoForm } from '../../components/events/EventoForm';
import { useCreateEvent } from '../../hooks/events';

export default function EventCreatePage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const create = useCreateEvent();

  return (
    <main style={{ maxWidth: 560, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <Link to="/me/events">← Mis eventos</Link>
      <h1>Crear evento</h1>
      <EventoForm
        submitLabel="Crear borrador"
        loading={create.isPending}
        serverError={serverError}
        onSubmit={async (data) => {
          setServerError(null);
          try {
            const created = await create.mutateAsync(data);
            navigate(`/events/${created.id}`, { replace: true });
          } catch (err) {
            setServerError(extractApiError(err).message);
          }
        }}
      />
    </main>
  );
}
