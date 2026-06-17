import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMe } from '../api/auth';
import { Button } from '../components/ui/Button';
import { useAuthStore } from '../stores/auth';
import type { User } from '../types/auth';

export default function ProfilePage() {
  const { user, setUser, logout } = useAuthStore();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!user);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) return;
    fetchMe()
      .then((me: User) => setUser(me))
      .catch(() => setError('No se pudo cargar el perfil'))
      .finally(() => setLoading(false));
  }, [user, setUser]);

  function onLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <main style={{ maxWidth: 480, margin: '4rem auto', fontFamily: 'system-ui' }}>
      <h1>Perfil</h1>
      {loading && <p>Cargando…</p>}
      {error && <p role="alert">{error}</p>}
      {user && (
        <dl>
          <dt>Email</dt>
          <dd>{user.email}</dd>
          <dt>Rol</dt>
          <dd>{user.role}</dd>
          <dt>Activo</dt>
          <dd>{user.is_active ? 'Sí' : 'No'}</dd>
        </dl>
      )}
      <Button onClick={onLogout}>Cerrar sesión</Button>
    </main>
  );
}
