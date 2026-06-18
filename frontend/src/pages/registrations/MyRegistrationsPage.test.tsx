import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import MyRegistrationsPage from './MyRegistrationsPage';
import type { RegistrationsPage } from '../../types/registration';

vi.mock('../../api/registrations', () => ({
  listMyRegistrations: vi.fn(),
  registerForEvent: vi.fn(),
  cancelMyRegistration: vi.fn(),
}));
import * as regApi from '../../api/registrations';

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MyRegistrationsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('MyRegistrationsPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('muestra mensaje cuando no hay inscripciones', async () => {
    const empty: RegistrationsPage = { items: [], total: 0, limit: 20, offset: 0 };
    vi.mocked(regApi.listMyRegistrations).mockResolvedValueOnce(empty);
    renderPage();
    await waitFor(() =>
      expect(screen.getByText(/aún no te has inscrito/i)).toBeInTheDocument(),
    );
  });

  it('lista historial con badges Confirmada y Cancelada', async () => {
    const page: RegistrationsPage = {
      items: [
        {
          id: 1,
          user_id: 5,
          event_id: 10,
          status: 'CONFIRMED',
          created_at: '2026-08-01T00:00:00Z',
          updated_at: '2026-08-01T00:00:00Z',
          event: {
            id: 10,
            title: 'Conf One',
            location: 'Quito',
            start_at: '2026-09-01T15:00:00Z',
            end_at: '2026-09-01T17:00:00Z',
            capacity: 50,
            status: 'PUBLISHED',
            owner_id: 9,
            confirmed_count: 5,
            is_full: false,
          },
        },
        {
          id: 2,
          user_id: 5,
          event_id: 20,
          status: 'CANCELLED',
          created_at: '2026-07-01T00:00:00Z',
          updated_at: '2026-07-02T00:00:00Z',
          event: {
            id: 20,
            title: 'Conf Two',
            location: 'Guayaquil',
            start_at: '2026-10-01T15:00:00Z',
            end_at: '2026-10-01T17:00:00Z',
            capacity: 80,
            status: 'CANCELLED',
            owner_id: 9,
            confirmed_count: 0,
            is_full: false,
          },
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    };
    vi.mocked(regApi.listMyRegistrations).mockResolvedValueOnce(page);
    renderPage();
    await waitFor(() => expect(screen.getByText('Conf One')).toBeInTheDocument());
    expect(screen.getByText('Conf Two')).toBeInTheDocument();
    expect(screen.getByText('Confirmada')).toBeInTheDocument();
    expect(screen.getByText('Cancelada')).toBeInTheDocument();
  });
});
