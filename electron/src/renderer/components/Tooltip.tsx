import type { ReactNode } from 'react';

export function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  return <span className="group relative inline-flex">
    {children}
    <span role="tooltip" className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-slate-950 px-2 py-1 text-[11px] text-slate-200 shadow-lg ring-1 ring-slate-700 group-hover:block group-focus-within:block">
      {label}
    </span>
  </span>;
}
