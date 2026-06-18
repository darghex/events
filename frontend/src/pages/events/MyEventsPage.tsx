import { useState } from 'react';
import { Link } from 'react-router-dom';
import { EventoCard } from '../../components/events/EventoCard';
import { Pagination } from '../../components/ui/Pagination';
import { useMyEvents } from '../../hooks/events';

const PAGE_SIZE = 20;

export default function MyEventsPage() {
  const [offset, setOffset] = useState(0);
  const { data, isLoading, isError } = useMyEvents({ limit: PAGE_SIZE, offset });

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Mis eventos</h1>
        <Link to="/events/new" style={{ color: '#2563eb' }}>
          + Crear evento
        </Link>
      </header>

      {isLoading && <p>Cargando…</p>}
      {isError && <p role="alert">No se pudieron cargar tus eventos</p>}
      {data && data.items.length === 0 && (
        <p>Aún no has creado eventos. Empieza con uno en borrador.</p>
      )}
      {data?.items.map((event) => <EventoCard key={event.id} event={event} />)}

      {data && data.total > PAGE_SIZE && (
        <Pagination total={data.total} limit={data.limit} offset={data.offset} onChange={setOffset} />
      )}
    </main>
  );
}
