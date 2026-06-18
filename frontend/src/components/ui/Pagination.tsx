import { Button } from './Button';

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onChange: (offset: number) => void;
}

export function Pagination({ total, limit, offset, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;
  const canPrev = offset > 0;
  const canNext = offset + limit < total;

  return (
    <nav
      aria-label="Paginación"
      style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '1rem' }}
    >
      <Button
        onClick={() => onChange(Math.max(0, offset - limit))}
        disabled={!canPrev}
        aria-label="Página anterior"
      >
        ← Anterior
      </Button>
      <span style={{ fontSize: '0.875rem', color: '#4b5563' }}>
        Página {currentPage} de {totalPages}
      </span>
      <Button
        onClick={() => onChange(offset + limit)}
        disabled={!canNext}
        aria-label="Página siguiente"
      >
        Siguiente →
      </Button>
    </nav>
  );
}
