import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { EventoForm } from '../../components/events/EventoForm';
import { useEventDetail, useUpdateEvent } from '../../hooks/events';

export default function EventEditPage() {
  const params = useParams<{ id: string }>();
  const id = params.id ? Number(params.id) : NaN;
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useEventDetail(Number.isNaN(id) ? undefined : id);
  const update = useUpdateEvent(id);
  const [serverError, setServerError] = useState<string | null>(null);

  if (isLoading) return <p style={{ padding: '2rem' }}>Cargando…</p>;
  if (isError || !data) {
    return (
      <main style={{ padding: '2rem' }}>
        <p role="alert">{extractApiError(error).message}</p>
        <Link to="/me/events">← Mis eventos</Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 560, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <Link to={`/events/${data.id}`}>← Volver al detalle</Link>
      <h1>Editar evento</h1>
      <EventoForm
        initial={data}
        submitLabel="Guardar cambios"
        loading={update.isPending}
        serverError={serverError}
        onSubmit={async (payload) => {
          setServerError(null);
          try {
            await update.mutateAsync(payload);
            navigate(`/events/${data.id}`, { replace: true });
          } catch (err) {
            setServerError(extractApiError(err).message);
          }
        }}
      />
    </main>
  );
}
