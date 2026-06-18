import { type FormEvent, useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { SpeakerPicker } from './SpeakerPicker';
import type { SessionCreateInput, SessionRead } from '../../types/session';
import type { UserSearchResult } from '../../types/user';

interface SessionFormProps {
  initial?: Partial<SessionRead>;
  submitLabel?: string;
  loading?: boolean;
  serverError?: string | null;
  onSubmit: (data: SessionCreateInput) => void;
}

function toLocalInput(iso: string | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInput(local: string): string {
  return new Date(local).toISOString();
}

export function SessionForm({
  initial,
  submitLabel = 'Guardar',
  loading = false,
  serverError = null,
  onSubmit,
}: SessionFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');
  const [speaker, setSpeaker] = useState<UserSearchResult | null>(
    initial?.speaker
      ? { id: initial.speaker.id, email: initial.speaker.email, role: 'ATTENDEE' }
      : null,
  );
  const [startLocal, setStartLocal] = useState(toLocalInput(initial?.start_at));
  const [endLocal, setEndLocal] = useState(toLocalInput(initial?.end_at));
  const [capacity, setCapacity] = useState<number | ''>(initial?.capacity ?? '');
  const [clientError, setClientError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setClientError(null);

    if (!title.trim()) {
      setClientError('El título es obligatorio');
      return;
    }
    if (!speaker) {
      setClientError('Debes seleccionar un ponente');
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
    if (capacity !== '' && capacity <= 0) {
      setClientError('La capacidad debe ser mayor a 0');
      return;
    }

    onSubmit({
      title: title.trim(),
      description: description?.trim() || null,
      speaker_id: speaker.id,
      start_at: startIso,
      end_at: endIso,
      capacity: capacity === '' ? null : capacity,
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
          maxLength={2000}
          rows={3}
          style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box' }}
        />
      </label>
      <SpeakerPicker value={speaker} onChange={setSpeaker} />
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
      <Input
        label="Capacidad (opcional)"
        name="capacity"
        type="number"
        min={1}
        value={capacity}
        onChange={(e) => {
          const raw = e.target.value;
          setCapacity(raw === '' ? '' : Number(raw));
        }}
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
