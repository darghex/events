import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { RequireAuth } from './components/RequireAuth';
import { RequireRole } from './components/RequireRole';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import RegisterPage from './pages/RegisterPage';
import EventCreatePage from './pages/events/EventCreatePage';
import EventDetailPage from './pages/events/EventDetailPage';
import EventEditPage from './pages/events/EventEditPage';
import EventsListPage from './pages/events/EventsListPage';
import MyEventsPage from './pages/events/MyEventsPage';
import SessionCreatePage from './pages/sessions/SessionCreatePage';
import SessionEditPage from './pages/sessions/SessionEditPage';
import MyRegistrationsPage from './pages/registrations/MyRegistrationsPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to="/events" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/events" element={<EventsListPage />} />
          <Route path="/events/new" element={<RequireRole roles={['ORGANIZER', 'ADMIN']}><EventCreatePage /></RequireRole>} />
          <Route path="/events/:id" element={<EventDetailPage />} />
          <Route
            path="/events/:id/edit"
            element={
              <RequireRole roles={['ORGANIZER', 'ADMIN']}>
                <EventEditPage />
              </RequireRole>
            }
          />
          <Route
            path="/events/:id/sessions/new"
            element={
              <RequireRole roles={['ORGANIZER', 'ADMIN']}>
                <SessionCreatePage />
              </RequireRole>
            }
          />
          <Route
            path="/events/:id/sessions/:sessionId/edit"
            element={
              <RequireRole roles={['ORGANIZER', 'ADMIN']}>
                <SessionEditPage />
              </RequireRole>
            }
          />
          <Route
            path="/me/events"
            element={
              <RequireRole roles={['ORGANIZER', 'ADMIN']}>
                <MyEventsPage />
              </RequireRole>
            }
          />
          <Route
            path="/profile"
            element={
              <RequireAuth>
                <ProfilePage />
              </RequireAuth>
            }
          />
          <Route
            path="/me/registrations"
            element={
              <RequireAuth>
                <MyRegistrationsPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/events" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
