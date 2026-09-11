import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Tooltip } from './Tooltip';

export function IconButton({ label, children, className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; children: ReactNode }) {
  return <Tooltip label={label}>
    <button {...props} aria-label={label} className={`inline-grid size-9 place-items-center rounded-md transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 disabled:cursor-not-allowed disabled:opacity-40 ${className}`}>
      {children}
    </button>
  </Tooltip>;
}
