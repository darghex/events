import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { SessionForm } from './SessionForm';
import type { SessionRead } from '../../types/session';

vi.mock('../../api/users', () => ({ searchUsers: vi.fn().mockResolvedValue([]) }));

function withQuery(node: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{node}</QueryClientProvider>;
}

const initialWithSpeaker: Partial<SessionRead> = {
  title: 'Charla A',
  description: 'Demo',
  start_at: '2026-09-01T15:00:00Z',
  end_at: '2026-09-01T16:00:00Z',
  capacity: 30,
  speaker_id: 5,
  speaker: { id: 5, email: 'sp@x.com' },
};

describe('SessionForm', () => {
  it('bloquea submit sin ponente seleccionado', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(withQuery(<SessionForm onSubmit={onSubmit} />));

    await user.type(screen.getByLabelText(/título/i), 'Charla');
    await user.type(screen.getByLabelText(/^inicio$/i), '2026-08-10T15:00');
    await user.type(screen.getByLabelText(/^fin$/i), '2026-08-10T16:00');
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/ponente/i);
  });

  it('rechaza fin <= inicio', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(withQuery(<SessionForm initial={initialWithSpeaker} onSubmit={onSubmit} />));

    const startInput = screen.getByLabelText(/^inicio$/i) as HTMLInputElement;
    const endInput = screen.getByLabelText(/^fin$/i) as HTMLInputElement;
    await user.clear(startInput);
    await user.type(startInput, '2026-09-01T18:00');
    await user.clear(endInput);
    await user.type(endInput, '2026-09-01T17:00');
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/inicio.*anterior.*fin/i);
  });

  it('llama onSubmit con payload normalizado cuando todo es válido', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(withQuery(<SessionForm initial={initialWithSpeaker} onSubmit={onSubmit} />));

    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const payload = onSubmit.mock.calls[0][0];
    expect(payload.title).toBe('Charla A');
    expect(payload.speaker_id).toBe(5);
    expect(payload.capacity).toBe(30);
  });

  it('capacidad vacía se envía como null', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(withQuery(<SessionForm initial={initialWithSpeaker} onSubmit={onSubmit} />));

    const capInput = screen.getByLabelText(/capacidad/i) as HTMLInputElement;
    await user.clear(capInput);
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0].capacity).toBeNull();
  });
});
