import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RequireAuth } from './RequireAuth';
import { useAuthStore } from '../stores/auth';

function renderRoutes(initial: string) {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path="/login" element={<div>login screen</div>} />
        <Route
          path="/protected"
          element={
            <RequireAuth>
              <div>protected content</div>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RequireAuth', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
  });

  it('redirige a /login cuando no hay sesión', () => {
    renderRoutes('/protected');
    expect(screen.getByText('login screen')).toBeInTheDocument();
  });

  it('renderiza children cuando hay accessToken', () => {
    useAuthStore.setState({ accessToken: 'fake-token' });
    renderRoutes('/protected');
    expect(screen.getByText('protected content')).toBeInTheDocument();
  });
});
