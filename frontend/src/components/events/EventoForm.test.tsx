import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { EventoForm } from './EventoForm';

describe('EventoForm', () => {
  it('rechaza fin anterior o igual a inicio y no llama onSubmit', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<EventoForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/título/i), 'Workshop');
    await user.type(screen.getByLabelText(/ubicación/i), 'Quito');
    await user.type(screen.getByLabelText(/capacidad/i), '30');
    await user.type(screen.getByLabelText(/^inicio$/i), '2026-08-10T15:00');
    await user.type(screen.getByLabelText(/^fin$/i), '2026-08-10T14:00');
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/inicio.*anterior.*fin/i);
  });

  it('rechaza capacidad <= 0', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<EventoForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/título/i), 'Workshop');
    await user.type(screen.getByLabelText(/ubicación/i), 'Quito');
    await user.type(screen.getByLabelText(/capacidad/i), '0');
    await user.type(screen.getByLabelText(/^inicio$/i), '2026-08-10T15:00');
    await user.type(screen.getByLabelText(/^fin$/i), '2026-08-10T17:00');
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/capacidad.*mayor a 0/i);
  });

  it('llama onSubmit con payload normalizado cuando todo es válido', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<EventoForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/título/i), '  Workshop  ');
    await user.type(screen.getByLabelText(/ubicación/i), 'Quito');
    await user.type(screen.getByLabelText(/capacidad/i), '50');
    await user.type(screen.getByLabelText(/^inicio$/i), '2026-08-10T15:00');
    await user.type(screen.getByLabelText(/^fin$/i), '2026-08-10T17:00');
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const payload = onSubmit.mock.calls[0][0];
    expect(payload.title).toBe('Workshop');
    expect(payload.location).toBe('Quito');
    expect(payload.capacity).toBe(50);
    expect(payload.start_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(payload.end_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });
});
