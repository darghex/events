import { type FormEvent, useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import type { EventCreateInput, EventRead } from '../../types/event';

interface EventoFormProps {
  initial?: Partial<EventRead>;
  submitLabel?: string;
  loading?: boolean;
  serverError?: string | null;
  onSubmit: (data: EventCreateInput) => void;
}

function toLocalInput(iso: string | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  // Convierte a YYYY-MM-DDTHH:mm en TZ local para <input type="datetime-local">
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInput(local: string): string {
  // Date interpreta el input en TZ local; toISOString lo emite con offset UTC ("Z")
  return new Date(local).toISOString();
}

export function EventoForm({
  initial,
  submitLabel = 'Guardar',
  loading = false,
  serverError = null,
  onSubmit,
}: EventoFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');
  const [location, setLocation] = useState(initial?.location ?? '');
  const [capacity, setCapacity] = useState<number | ''>(initial?.capacity ?? '');
  const [startLocal, setStartLocal] = useState(toLocalInput(initial?.start_at));
  const [endLocal, setEndLocal] = useState(toLocalInput(initial?.end_at));
  const [clientError, setClientError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setClientError(null);

    if (!title.trim()) {
      setClientError('El título es obligatorio');
      return;
    }
    if (!location.trim()) {
      setClientError('La ubicación es obligatoria');
      return;
    }
    if (typeof capacity !== 'number' || capacity <= 0) {
      setClientError('La capacidad debe ser mayor a 0');
      return;
    }
    if (!startLocal || !endLocal) {
      setClientError('Fechas de inicio y fin son obligatorias');
      return;
    }
    const startIso = fromLocalInput(startLocal);
    const endIso = fromLocalInput(endLocal);
    if (new Date(startIso) >= new Date(endIso)) {
      setClientError('La fecha de inicio debe ser anterior a la de fin');
      return;
    }

    onSubmit({
      title: title.trim(),
      description: description.trim() || null,
      location: location.trim(),
      capacity,
      start_at: startIso,
      end_at: endIso,
    });
  }

  const errorMessage = clientError ?? serverError;

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Input
        label="Título"
        name="title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={200}
        required
      />
      <label htmlFor="description" style={{ display: 'block', marginBottom: '0.75rem' }}>
        <span style={{ display: 'block', marginBottom: '0.25rem' }}>Descripción</span>
        <textarea
          id="description"
          name="description"
          value={description ?? ''}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={5000}
          rows={4}
          style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box' }}
        />
      </label>
      <Input
        label="Ubicación"
        name="location"
        value={location}
        onChange={(e) => setLocation(e.target.value)}
        maxLength={200}
        required
      />
      <Input
        label="Capacidad"
        name="capacity"
        type="number"
        min={1}
        value={capacity}
        onChange={(e) => {
          const raw = e.target.value;
          setCapacity(raw === '' ? '' : Number(raw));
        }}
        required
      />
      <Input
        label="Inicio"
        name="start_at"
        type="datetime-local"
        value={startLocal}
        onChange={(e) => setStartLocal(e.target.value)}
        required
      />
      <Input
        label="Fin"
        name="end_at"
        type="datetime-local"
        value={endLocal}
        onChange={(e) => setEndLocal(e.target.value)}
        required
      />
      {errorMessage && (
        <p role="alert" style={{ color: '#c00' }}>
          {errorMessage}
        </p>
      )}
      <Button type="submit" disabled={loading}>
        {loading ? 'Guardando…' : submitLabel}
      </Button>
    </form>
  );
}
