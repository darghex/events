import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the placeholder title', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /mis eventos/i })).toBeInTheDocument();
  });
});
