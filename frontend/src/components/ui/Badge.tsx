import type { EventStatus } from '../../types/event';

const COLORS: Record<EventStatus, { bg: string; fg: string; label: string }> = {
  DRAFT: { bg: '#e5e7eb', fg: '#1f2937', label: 'Borrador' },
  PUBLISHED: { bg: '#dcfce7', fg: '#166534', label: 'Publicado' },
  IN_PROGRESS: { bg: '#dbeafe', fg: '#1e40af', label: 'En progreso' },
  FINISHED: { bg: '#e5e7eb', fg: '#374151', label: 'Finalizado' },
  CANCELLED: { bg: '#fee2e2', fg: '#991b1b', label: 'Cancelado' },
};

export function StatusBadge({ status }: { status: EventStatus }) {
  const { bg, fg, label } = COLORS[status];
  return (
    <span
      data-testid="status-badge"
      style={{
        display: 'inline-block',
        padding: '0.125rem 0.5rem',
        borderRadius: '999px',
        background: bg,
        color: fg,
        fontSize: '0.75rem',
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
}
