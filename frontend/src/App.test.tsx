import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';
import { useAuthStore } from './stores/auth';

// El home pasó a ser el listado público de eventos; mockea el fetch para evitar red real.
vi.mock('./api/events', () => ({
  listEvents: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 }),
  listMyEvents: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 }),
  getEvent: vi.fn(),
  createEvent: vi.fn(),
  updateEvent: vi.fn(),
  deleteEvent: vi.fn(),
}));

describe('App', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
  });

  it('muestra el listado público de eventos en la raíz sin sesión', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /^eventos$/i })).toBeInTheDocument();
  });
});
