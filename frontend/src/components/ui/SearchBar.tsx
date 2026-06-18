import { useEffect, useState } from 'react';

interface SearchBarProps {
  initialValue?: string;
  placeholder?: string;
  onSearch: (value: string) => void;
  debounceMs?: number;
}

export function SearchBar({
  initialValue = '',
  placeholder = 'Buscar…',
  onSearch,
  debounceMs = 300,
}: SearchBarProps) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    const handle = setTimeout(() => onSearch(value.trim()), debounceMs);
    return () => clearTimeout(handle);
  }, [value, debounceMs, onSearch]);

  return (
    <input
      type="search"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder={placeholder}
      aria-label="Buscar eventos"
      style={{
        width: '100%',
        padding: '0.5rem',
        marginBottom: '1rem',
        border: '1px solid #d1d5db',
        borderRadius: '6px',
        boxSizing: 'border-box',
      }}
    />
  );
}
