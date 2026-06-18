import { Link, useNavigate, useParams } from 'react-router-dom';
import { extractApiError } from '../../api/errors';
import { EventTransitionsBar } from '../../components/events/EventTransitionsBar';
import { RegistrationButton } from '../../components/events/RegistrationButton';
import { SessionsAgenda } from '../../components/sessions/SessionsAgenda';
import { StatusBadge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useDeleteEvent, useEventDetail } from '../../hooks/events';
import { useAuthStore } from '../../stores/auth';

function formatRange(start: string, end: string): string {
  const fmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'full', timeStyle: 'short' });
  return `${fmt.format(new Date(start))} – ${fmt.format(new Date(end))}`;
}

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id ? Number(params.id) : undefined;
  const { data, isLoading, isError, error } = useEventDetail(id);
  const { user } = useAuthStore();
  const deleteMutation = useDeleteEvent();
  const navigate = useNavigate();

  if (isLoading) return <p style={{ padding: '2rem' }}>Cargando…</p>;
  if (isError || !data) {
    const message = extractApiError(error).message;
    return (
      <main style={{ padding: '2rem' }}>
        <p role="alert">{message}</p>
        <Link to="/events">← Volver al listado</Link>
      </main>
    );
  }

  const canMutate =
    !!user && (user.id === data.owner_id || user.role === 'ADMIN') && data.status === 'DRAFT';
  const canAdminEdit = !!user && user.role === 'ADMIN';

  async function onDelete() {
    if (!data || !confirm('¿Eliminar este evento?')) return;
    try {
      await deleteMutation.mutateAsync(data.id);
      navigate('/me/events', { replace: true });
    } catch (err) {
      alert(extractApiError(err).message);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <Link to="/events">← Volver al listado</Link>
      <header style={{ marginTop: '1rem', display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
        <h1 style={{ margin: 0 }}>{data.title}</h1>
        <StatusBadge status={data.status} />
      </header>
      <EventTransitionsBar event={data} user={user ?? null} />
      <RegistrationButton event={data} user={user ?? null} />
      <p style={{ color: '#4b5563' }}>{data.location}</p>
      <p style={{ color: '#4b5563' }}>{formatRange(data.start_at, data.end_at)}</p>
      <p style={{ color: '#6b7280' }}>Capacidad: {data.capacity}</p>
      {data.description && <p style={{ marginTop: '1rem' }}>{data.description}</p>}

      {(canMutate || canAdminEdit) && (
        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem' }}>
          <Link to={`/events/${data.id}/edit`}>
            <Button>Editar</Button>
          </Link>
          {canMutate && (
            <Button onClick={onDelete} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? 'Eliminando…' : 'Eliminar'}
            </Button>
          )}
        </div>
      )}

      <SessionsAgenda event={data} user={user ?? null} />
    </main>
  );
}
