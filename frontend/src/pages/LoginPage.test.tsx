import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import LoginPage from './LoginPage';

vi.mock('../api/auth', () => ({
  login: vi.fn().mockResolvedValue({
    access_token: 'a',
    refresh_token: 'r',
    token_type: 'bearer',
  }),
  fetchMe: vi.fn().mockResolvedValue({
    id: 1,
    email: 'u@example.com',
    role: 'ATTENDEE',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  }),
}));

describe('LoginPage', () => {
  it('renderiza el formulario y dispara login al enviar', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
    await user.type(screen.getByLabelText(/email/i), 'u@example.com');
    await user.type(screen.getByLabelText(/contraseña/i), 'ValidPass1');
    await user.click(screen.getByRole('button', { name: /ingresar/i }));

    const { login } = await import('../api/auth');
    expect(login).toHaveBeenCalledWith('u@example.com', 'ValidPass1');
  });
});
