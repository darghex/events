import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { EventTransitionsBar } from './EventTransitionsBar';
import type { EventRead, EventStatus } from '../../types/event';
import type { User } from '../../types/auth';

vi.mock('../../api/events', () => ({
  transitionEvent: vi.fn().mockResolvedValue({}),
  // Reexportar funciones que el módulo de hooks importa también:
  createEvent: vi.fn(),
  deleteEvent: vi.fn(),
  getEvent: vi.fn(),
  listEvents: vi.fn(),
  listMyEvents: vi.fn(),
  updateEvent: vi.fn(),
}));

import * as eventsApi from '../../api/events';

function makeEvent(status: EventStatus, ownerId = 1): EventRead {
  return {
    id: 10,
    title: 'Conf',
    description: null,
    location: 'Quito',
    capacity: 100,
    start_at: '2026-09-01T15:00:00Z',
    end_at: '2026-09-01T17:00:00Z',
    status,
    owner_id: ownerId,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function makeUser(role: User['role'], id = 1): User {
  return { id, email: 'u@x.com', role, is_active: true, created_at: '2026-01-01T00:00:00Z' };
}

function renderBar(event: EventRead, user: User | null) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <EventTransitionsBar event={event} user={user} />
    </QueryClientProvider>,
  );
}

describe('EventTransitionsBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Draft + owner muestra "Publicar" y "Cancelar"', () => {
    renderBar(makeEvent('DRAFT'), makeUser('ORGANIZER'));
    expect(screen.getByRole('button', { name: 'Publicar' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeInTheDocument();
  });

  it('Published + owner muestra "Iniciar" y "Cancelar"', () => {
    renderBar(makeEvent('PUBLISHED'), makeUser('ORGANIZER'));
    expect(screen.getByRole('button', { name: 'Iniciar' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeInTheDocument();
  });

  it('InProgress + owner muestra solo "Finalizar"', () => {
    renderBar(makeEvent('IN_PROGRESS'), makeUser('ORGANIZER'));
    expect(screen.getByRole('button', { name: 'Finalizar' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Cancelar' })).not.toBeInTheDocument();
  });

  it('Finished (terminal) no renderiza la barra', () => {
    renderBar(makeEvent('FINISHED'), makeUser('ORGANIZER'));
    expect(screen.queryByTestId('event-transitions-bar')).not.toBeInTheDocument();
  });

  it('Cancelled (terminal) no renderiza la barra', () => {
    renderBar(makeEvent('CANCELLED'), makeUser('ORGANIZER'));
    expect(screen.queryByTestId('event-transitions-bar')).not.toBeInTheDocument();
  });

  it('Attendee no-owner no renderiza la barra', () => {
    renderBar(makeEvent('DRAFT'), makeUser('ATTENDEE', 99));
    expect(screen.queryByTestId('event-transitions-bar')).not.toBeInTheDocument();
  });

  it('Organizer no-owner no renderiza la barra', () => {
    renderBar(makeEvent('DRAFT', /*ownerId*/ 1), makeUser('ORGANIZER', /*userId*/ 99));
    expect(screen.queryByTestId('event-transitions-bar')).not.toBeInTheDocument();
  });

  it('Admin sobre evento ajeno SÍ renderiza acciones', () => {
    renderBar(makeEvent('DRAFT', /*ownerId*/ 1), makeUser('ADMIN', /*userId*/ 99));
    expect(screen.getByRole('button', { name: 'Publicar' })).toBeInTheDocument();
  });

  it('Sin sesión no renderiza la barra', () => {
    renderBar(makeEvent('DRAFT'), null);
    expect(screen.queryByTestId('event-transitions-bar')).not.toBeInTheDocument();
  });

  it('Click en "Cancelar" pide confirmación antes de mutar', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const user = userEvent.setup();
    renderBar(makeEvent('DRAFT'), makeUser('ORGANIZER'));

    await user.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(eventsApi.transitionEvent).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('Click en "Publicar" llama al backend sin confirmar', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm');
    const user = userEvent.setup();
    renderBar(makeEvent('DRAFT'), makeUser('ORGANIZER'));

    await user.click(screen.getByRole('button', { name: 'Publicar' }));

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(eventsApi.transitionEvent).toHaveBeenCalledWith(10, 'PUBLISHED');
    confirmSpy.mockRestore();
  });
});
