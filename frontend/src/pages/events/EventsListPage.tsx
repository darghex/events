import { useState } from 'react';
import { Link } from 'react-router-dom';
import { EventoCard } from '../../components/events/EventoCard';
import { Pagination } from '../../components/ui/Pagination';
import { SearchBar } from '../../components/ui/SearchBar';
import { useEventsList } from '../../hooks/events';
import { useAuthStore } from '../../stores/auth';

const PAGE_SIZE = 20;

export default function EventsListPage() {
  const [q, setQ] = useState('');
  const [offset, setOffset] = useState(0);
  const { user } = useAuthStore();
  const canCreate = user?.role === 'ORGANIZER' || user?.role === 'ADMIN';

  const { data, isLoading, isError } = useEventsList({ q: q || undefined, limit: PAGE_SIZE, offset });

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Eventos</h1>
        {canCreate && (
          <Link to="/events/new" style={{ color: '#2563eb' }}>
            + Crear evento
          </Link>
        )}
      </header>

      <SearchBar
        placeholder="Buscar por título…"
        onSearch={(value) => {
          setQ(value);
          setOffset(0);
        }}
      />

      {isLoading && <p>Cargando eventos…</p>}
      {isError && <p role="alert">No se pudieron cargar los eventos</p>}
      {data && data.items.length === 0 && <p>No hay eventos publicados.</p>}
      {data?.items.map((event) => <EventoCard key={event.id} event={event} />)}

      {data && data.total > PAGE_SIZE && (
        <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
      )}
    </main>
  );
}
