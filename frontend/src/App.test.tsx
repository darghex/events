import { render, screen } from '@testing-library/react';
import App from './App';
import { useAuthStore } from './stores/auth';

describe('App', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
  });

  it('redirige rutas protegidas a /login cuando no hay sesión', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /iniciar sesión/i })).toBeInTheDocument();
  });
});
