import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';

export function Navbar() {
  const { user, accessToken, refreshToken, logout } = useAuthStore();
  const navigate = useNavigate();
  const isAuthed = !!(accessToken || refreshToken);
  const canManage = user?.role === 'ORGANIZER' || user?.role === 'ADMIN';

  function onLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <nav
      style={{
        display: 'flex',
        gap: '1rem',
        padding: '0.75rem 1.5rem',
        borderBottom: '1px solid #e5e7eb',
        background: '#fafafa',
        fontFamily: 'system-ui',
      }}
    >
      <Link to="/events">Eventos</Link>
      {canManage && <Link to="/me/events">Mis eventos</Link>}
      {isAuthed && <Link to="/me/registrations">Mis inscripciones</Link>}
      <span style={{ flex: 1 }} />
      {isAuthed ? (
        <>
          <Link to="/profile">{user?.email ?? 'Perfil'}</Link>
          <button type="button" onClick={onLogout} style={{ cursor: 'pointer' }}>
            Salir
          </button>
        </>
      ) : (
        <>
          <Link to="/login">Login</Link>
          <Link to="/register">Registro</Link>
        </>
      )}
    </nav>
  );
}
