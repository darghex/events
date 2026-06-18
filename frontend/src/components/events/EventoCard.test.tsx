import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { EventoCard } from './EventoCard';
import type { EventListItem } from '../../types/event';

const baseEvent: EventListItem = {
  id: 42,
  title: 'React Summit',
  location: 'Quito',
  start_at: '2026-08-10T15:00:00Z',
  end_at: '2026-08-10T18:00:00Z',
  capacity: 200,
  status: 'PUBLISHED',
  owner_id: 1,
};

describe('EventoCard', () => {
  it('renderiza título, ubicación, capacidad y badge de estado', () => {
    render(
      <MemoryRouter>
        <EventoCard event={baseEvent} />
      </MemoryRouter>,
    );
    expect(screen.getByRole('heading', { name: /react summit/i })).toBeInTheDocument();
    expect(screen.getByText('Quito')).toBeInTheDocument();
    expect(screen.getByText(/capacidad: 200/i)).toBeInTheDocument();
    expect(screen.getByTestId('status-badge')).toHaveTextContent(/publicado/i);
  });

  it('apunta al detalle del evento', () => {
    render(
      <MemoryRouter>
        <EventoCard event={baseEvent} />
      </MemoryRouter>,
    );
    const link = screen.getByRole('link', { name: /react summit/i });
    expect(link).toHaveAttribute('href', '/events/42');
  });

  it('muestra badge Borrador para eventos en DRAFT', () => {
    render(
      <MemoryRouter>
        <EventoCard event={{ ...baseEvent, status: 'DRAFT' }} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId('status-badge')).toHaveTextContent(/borrador/i);
  });
});
