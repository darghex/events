import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { SessionForm } from '../../components/sessions/SessionForm';
import { useCreateSession } from '../../hooks/sessions';

export default function SessionCreatePage() {
  const params = useParams<{ id: string }>();
  const eventId = params.id ? Number(params.id) : NaN;
  const navigate = useNavigate();
  const create = useCreateSession(eventId);
  const [serverError, setServerError] = useState<string | null>(null);

  return (
    <main style={{ maxWidth: 560, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <Link to={`/events/${eventId}`}>← Volver al evento</Link>
      <h1>Añadir sesión</h1>
      <SessionForm
        submitLabel="Crear sesión"
        loading={create.isPending}
        serverError={serverError}
        onSubmit={async (data) => {
          setServerError(null);
          try {
            await create.mutateAsync(data);
            navigate(`/events/${eventId}`, { replace: true });
          } catch (err) {
            setServerError(extractApiError(err).message);
          }
        }}
      />
    </main>
  );
}
