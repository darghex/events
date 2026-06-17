import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export function Input({ label, id, ...rest }: InputProps) {
  const inputId = id ?? rest.name;
  return (
    <label htmlFor={inputId} style={{ display: 'block', marginBottom: '0.75rem' }}>
      <span style={{ display: 'block', marginBottom: '0.25rem' }}>{label}</span>
      <input
        id={inputId}
        {...rest}
        style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box' }}
      />
    </label>
  );
}
