import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { SpeakerPicker } from './SpeakerPicker';

vi.mock('../../api/users', () => ({ searchUsers: vi.fn() }));
import * as usersApi from '../../api/users';

function renderPicker(onChange = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const ret = render(
    <QueryClientProvider client={qc}>
      <SpeakerPicker value={null} onChange={onChange} />
    </QueryClientProvider>,
  );
  return { ...ret, onChange };
}

describe('SpeakerPicker', () => {
  beforeEach(() => vi.clearAllMocks());

  it('no dispara búsqueda con menos de 2 caracteres', async () => {
    const user = userEvent.setup();
    renderPicker();
    await user.type(screen.getByLabelText(/buscar ponente/i), 'a');
    // Esperamos al debounce
    await new Promise((r) => setTimeout(r, 400));
    expect(usersApi.searchUsers).not.toHaveBeenCalled();
  });

  it('muestra opciones tras debounce y permite seleccionar', async () => {
    vi.mocked(usersApi.searchUsers).mockResolvedValueOnce([
      { id: 1, email: 'alice@x.com', role: 'ATTENDEE' },
    ]);
    const user = userEvent.setup();
    const { onChange } = renderPicker();
    await user.type(screen.getByLabelText(/buscar ponente/i), 'al');
    await waitFor(() => expect(usersApi.searchUsers).toHaveBeenCalled(), { timeout: 1500 });
    const option = await screen.findByRole('button', { name: /alice@x.com/i });
    await user.click(option);
    expect(onChange).toHaveBeenCalledWith({ id: 1, email: 'alice@x.com', role: 'ATTENDEE' });
  });

  it('muestra mensaje fallback cuando no hay resultados', async () => {
    vi.mocked(usersApi.searchUsers).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    renderPicker();
    await user.type(screen.getByLabelText(/buscar ponente/i), 'zz');
    await waitFor(() => expect(usersApi.searchUsers).toHaveBeenCalled(), { timeout: 1500 });
    expect(await screen.findByTestId('speaker-fallback')).toBeInTheDocument();
  });

  it('renderiza estado seleccionado y permite cambiar', async () => {
    const onChange = vi.fn();
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <SpeakerPicker
          value={{ id: 5, email: 'bob@x.com', role: 'ATTENDEE' }}
          onChange={onChange}
        />
      </QueryClientProvider>,
    );
    expect(screen.getByTestId('speaker-selected')).toHaveTextContent('bob@x.com');
    await userEvent.setup().click(screen.getByRole('button', { name: /quitar ponente/i }));
    expect(onChange).toHaveBeenCalledWith(null);
  });
});
