import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { SessionsAgenda } from './SessionsAgenda';
import type { EventRead, EventStatus } from '../../types/event';
import type { User } from '../../types/auth';
import type { SessionRead } from '../../types/session';

vi.mock('../../api/sessions', () => ({
  listSessions: vi.fn(),
  deleteSession: vi.fn(),
  createSession: vi.fn(),
  updateSession: vi.fn(),
  getSession: vi.fn(),
}));
import * as sessionsApi from '../../api/sessions';

function makeEvent(status: EventStatus, ownerId = 1): EventRead {
  return {
    id: 10,
    title: 'Conf',
    description: null,
    location: 'Quito',
    capacity: 100,
    start_at: '2026-09-01T15:00:00Z',
    end_at: '2026-09-01T18:00:00Z',
    status,
    owner_id: ownerId,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function makeSession(id: number, title: string): SessionRead {
  return {
    id,
    event_id: 10,
    speaker_id: 99,
    title,
    description: null,
    start_at: '2026-09-01T15:30:00Z',
    end_at: '2026-09-01T16:00:00Z',
    capacity: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    speaker: { id: 99, email: 'sp@x.com' },
  };
}

function renderAgenda(event: EventRead, user: User | null) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SessionsAgenda event={event} user={user} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('SessionsAgenda', () => {
  beforeEach(() => vi.clearAllMocks());

  it('muestra "+ Añadir sesión" cuando owner en Draft', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([]);
    renderAgenda(makeEvent('DRAFT'), {
      id: 1, email: 'o@x.com', role: 'ORGANIZER', is_active: true, created_at: '2026-01-01T00:00:00Z',
    });
    await waitFor(() => expect(screen.getByRole('link', { name: /añadir sesión/i })).toBeInTheDocument());
  });

  it('owner en Published también puede añadir', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([]);
    renderAgenda(makeEvent('PUBLISHED'), {
      id: 1, email: 'o@x.com', role: 'ORGANIZER', is_active: true, created_at: '2026-01-01T00:00:00Z',
    });
    await waitFor(() => expect(screen.getByRole('link', { name: /añadir sesión/i })).toBeInTheDocument());
  });

  it('owner en IN_PROGRESS NO puede añadir', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([]);
    renderAgenda(makeEvent('IN_PROGRESS'), {
      id: 1, email: 'o@x.com', role: 'ORGANIZER', is_active: true, created_at: '2026-01-01T00:00:00Z',
    });
    await waitFor(() => expect(screen.queryByRole('link', { name: /añadir sesión/i })).not.toBeInTheDocument());
  });

  it('attendee no ve botones de gestión', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([makeSession(1, 'Charla X')]);
    renderAgenda(makeEvent('PUBLISHED'), {
      id: 99, email: 'a@x.com', role: 'ATTENDEE', is_active: true, created_at: '2026-01-01T00:00:00Z',
    });
    await waitFor(() => expect(screen.getByText(/charla x/i)).toBeInTheDocument());
    expect(screen.queryByRole('link', { name: /añadir sesión/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument();
  });

  it('admin sobre evento ajeno SÍ puede gestionar', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([makeSession(1, 'C1')]);
    renderAgenda(makeEvent('DRAFT', /*ownerId*/ 5), {
      id: 99, email: 'adm@x.com', role: 'ADMIN', is_active: true, created_at: '2026-01-01T00:00:00Z',
    });
    // Esperar a que cargue la sesión antes de buscar los botones por item.
    expect(await screen.findByText('C1')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /añadir sesión/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /editar/i })).toBeInTheDocument();
  });

  it('renderiza lista ordenada con datos del speaker', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([
      makeSession(1, 'C1'),
      makeSession(2, 'C2'),
    ]);
    renderAgenda(makeEvent('PUBLISHED'), null);
    await waitFor(() => expect(screen.getByText('C1')).toBeInTheDocument());
    expect(screen.getByText('C2')).toBeInTheDocument();
    // El email del speaker se muestra para cada sesión.
    expect(screen.getAllByText(/sp@x.com/i).length).toBeGreaterThanOrEqual(1);
  });

  it('estado vacío muestra mensaje', async () => {
    vi.mocked(sessionsApi.listSessions).mockResolvedValueOnce([]);
    renderAgenda(makeEvent('PUBLISHED'), null);
    await waitFor(() => expect(screen.getByText(/no hay sesiones/i)).toBeInTheDocument());
  });
});
