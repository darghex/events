import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { RegistrationButton } from './RegistrationButton';
import type { EventRead, EventStatus, RegistrationStatus } from '../../types/event';
import type { User } from '../../types/auth';

vi.mock('../../api/registrations', () => ({
  registerForEvent: vi.fn().mockResolvedValue({}),
  cancelMyRegistration: vi.fn().mockResolvedValue(undefined),
  listMyRegistrations: vi.fn(),
}));
import * as regApi from '../../api/registrations';

function makeEvent(
  status: EventStatus,
  opts: { is_full?: boolean; my_status?: RegistrationStatus | null; capacity?: number; count?: number } = {},
): EventRead {
  return {
    id: 7,
    title: 'Conf',
    description: null,
    location: 'Quito',
    capacity: opts.capacity ?? 100,
    start_at: '2026-09-01T15:00:00Z',
    end_at: '2026-09-01T17:00:00Z',
    status,
    owner_id: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    confirmed_count: opts.count ?? 0,
    is_full: opts.is_full ?? false,
    my_registration_status: opts.my_status ?? null,
  };
}

function makeUser(): User {
  return { id: 5, email: 'a@x.com', role: 'ATTENDEE', is_active: true, created_at: '2026-01-01T00:00:00Z' };
}

function renderButton(event: EventRead, user: User | null) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <RegistrationButton event={event} user={user} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('RegistrationButton', () => {
  beforeEach(() => vi.clearAllMocks());

  it('sin sesión muestra link a login y conteo', () => {
    renderButton(makeEvent('PUBLISHED', { count: 3, capacity: 10 }), null);
    expect(screen.getByText(/inicia sesión/i)).toBeInTheDocument();
    expect(screen.getByText('3 / 10')).toBeInTheDocument();
  });

  it('evento Draft muestra mensaje de no-disponible (sin botón)', () => {
    renderButton(makeEvent('DRAFT'), makeUser());
    expect(screen.getByText(/no disponibles/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /inscribirme/i })).not.toBeInTheDocument();
  });

  it('Published + no inscrito + no full muestra "Inscribirme" y llama mutación', async () => {
    const user = userEvent.setup();
    renderButton(makeEvent('PUBLISHED'), makeUser());
    await user.click(screen.getByRole('button', { name: /inscribirme/i }));
    expect(regApi.registerForEvent).toHaveBeenCalledWith(7);
  });

  it('Published + lleno muestra "Cupo lleno" disabled', () => {
    renderButton(makeEvent('PUBLISHED', { is_full: true, count: 10, capacity: 10 }), makeUser());
    const btn = screen.getByRole('button', { name: /cupo lleno/i });
    expect(btn).toBeDisabled();
  });

  it('Confirmed muestra "Cancelar mi inscripción" y pide confirmación', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const user = userEvent.setup();
    renderButton(makeEvent('PUBLISHED', { my_status: 'CONFIRMED' }), makeUser());
    await user.click(screen.getByRole('button', { name: /cancelar mi inscripción/i }));
    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(regApi.cancelMyRegistration).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('Confirmed + confirma → llama cancelMyRegistration', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const user = userEvent.setup();
    renderButton(makeEvent('PUBLISHED', { my_status: 'CONFIRMED' }), makeUser());
    await user.click(screen.getByRole('button', { name: /cancelar mi inscripción/i }));
    expect(regApi.cancelMyRegistration).toHaveBeenCalledWith(7);
    confirmSpy.mockRestore();
  });

  it('prioriza "Cancelar" sobre "Cupo lleno" cuando ya estoy inscrito', () => {
    renderButton(
      makeEvent('PUBLISHED', { is_full: true, my_status: 'CONFIRMED', count: 10, capacity: 10 }),
      makeUser(),
    );
    expect(screen.getByRole('button', { name: /cancelar mi inscripción/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /cupo lleno/i })).not.toBeInTheDocument();
  });
});
