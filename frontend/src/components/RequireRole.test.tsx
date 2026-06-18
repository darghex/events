import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RequireRole } from './RequireRole';
import { useAuthStore } from '../stores/auth';
import type { UserRole } from '../types/auth';

function renderRoutes(initial: string, roles: UserRole[]) {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path="/login" element={<div>login screen</div>} />
        <Route path="/events" element={<div>public events</div>} />
        <Route
          path="/protected"
          element={
            <RequireRole roles={roles}>
              <div>only for elite</div>
            </RequireRole>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RequireRole', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
  });

  it('redirige a /login cuando no hay sesión', () => {
    renderRoutes('/protected', ['ORGANIZER']);
    expect(screen.getByText('login screen')).toBeInTheDocument();
  });

  it('redirige a /events cuando el rol del usuario no aplica', () => {
    useAuthStore.setState({
      accessToken: 'x',
      user: { id: 1, email: 'a@a.com', role: 'ATTENDEE', is_active: true, created_at: '2026-01-01T00:00:00Z' },
    });
    renderRoutes('/protected', ['ORGANIZER', 'ADMIN']);
    expect(screen.getByText('public events')).toBeInTheDocument();
  });

  it('renderiza children cuando el rol coincide', () => {
    useAuthStore.setState({
      accessToken: 'x',
      user: {
        id: 1,
        email: 'org@a.com',
        role: 'ORGANIZER',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
    });
    renderRoutes('/protected', ['ORGANIZER', 'ADMIN']);
    expect(screen.getByText('only for elite')).toBeInTheDocument();
  });
});
