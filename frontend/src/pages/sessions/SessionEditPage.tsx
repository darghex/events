import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { SessionForm } from '../../components/sessions/SessionForm';
import { useSession, useUpdateSession } from '../../hooks/sessions';

export default function SessionEditPage() {
  const params = useParams<{ id: string; sessionId: string }>();
  const eventId = params.id ? Number(params.id) : NaN;
  const sessionId = params.sessionId ? Number(params.sessionId) : NaN;
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useSession(eventId, sessionId);
  const update = useUpdateSession(eventId, sessionId);
  const [serverError, setServerError] = useState<string | null>(null);

  if (isLoading) return <p style={{ padding: '2rem' }}>Cargando…</p>;
  if (isError || !data) {
    return (
      <main style={{ padding: '2rem' }}>
        <p role="alert">{extractApiError(error).message}</p>
        <Link to={`/events/${eventId}`}>← Volver al evento</Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 560, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <Link to={`/events/${eventId}`}>← Volver al evento</Link>
      <h1>Editar sesión</h1>
      <SessionForm
        initial={data}
        submitLabel="Guardar cambios"
        loading={update.isPending}
        serverError={serverError}
        onSubmit={async (payload) => {
          setServerError(null);
          try {
            await update.mutateAsync(payload);
            navigate(`/events/${eventId}`, { replace: true });
          } catch (err) {
            setServerError(extractApiError(err).message);
          }
        }}
      />
    </main>
  );
}
