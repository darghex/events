import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import EventsListPage from './EventsListPage';
import type { EventsPage } from '../../types/event';

vi.mock('../../api/events', () => ({
  listEvents: vi.fn(),
  listMyEvents: vi.fn(),
}));

import * as eventsApi from '../../api/events';

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EventsListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('EventsListPage', () => {
  it('muestra "no hay eventos" cuando la API responde vacío', async () => {
    const empty: EventsPage = { items: [], total: 0, limit: 20, offset: 0 };
    vi.mocked(eventsApi.listEvents).mockResolvedValueOnce(empty);
    renderPage();
    await waitFor(() => expect(screen.getByText(/no hay eventos publicados/i)).toBeInTheDocument());
  });

  it('renderiza tarjetas para cada evento publicado', async () => {
    const page: EventsPage = {
      items: [
        {
          id: 1,
          title: 'Conf One',
          location: 'Quito',
          start_at: '2026-09-01T15:00:00Z',
          end_at: '2026-09-01T17:00:00Z',
          capacity: 50,
          status: 'PUBLISHED',
          owner_id: 9,
        },
        {
          id: 2,
          title: 'Conf Two',
          location: 'Guayaquil',
          start_at: '2026-10-01T15:00:00Z',
          end_at: '2026-10-01T17:00:00Z',
          capacity: 80,
          status: 'PUBLISHED',
          owner_id: 9,
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    };
    vi.mocked(eventsApi.listEvents).mockResolvedValueOnce(page);
    renderPage();
    await waitFor(() => expect(screen.getByRole('heading', { name: /conf one/i })).toBeInTheDocument());
    expect(screen.getByRole('heading', { name: /conf two/i })).toBeInTheDocument();
  });
});
