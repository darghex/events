import type { ButtonHTMLAttributes } from 'react';

export function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      {...props}
      style={{
        padding: '0.5rem 1rem',
        cursor: 'pointer',
        border: '1px solid #333',
        background: '#111',
        color: '#fff',
        borderRadius: '4px',
        ...props.style,
      }}
    />
  );
}
