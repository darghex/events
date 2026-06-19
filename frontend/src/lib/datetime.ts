/**
 * Helpers de fecha/hora para formularios con `<input type="datetime-local">`.
 *
 * El input nativo trabaja en TZ del navegador y emite `YYYY-MM-DDTHH:mm` sin
 * offset. Estos helpers traducen al/del ISO-8601 con offset que la API
 * espera (ver convención global en CLAUDE.md raíz).
 */

/** ISO-8601 (con offset Z o ±HH:mm) → `YYYY-MM-DDTHH:mm` en TZ local. */
export function toLocalInput(iso: string | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** `YYYY-MM-DDTHH:mm` (interpretado en TZ local) → ISO-8601 con offset UTC. */
export function fromLocalInput(local: string): string {
  return new Date(local).toISOString();
}
