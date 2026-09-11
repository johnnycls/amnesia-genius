import type { ReactNode } from 'react';

export function EmptyState({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  return <div className="grid h-full place-items-center text-center"><div className="max-w-sm"><div className="mx-auto mb-4 grid size-12 place-items-center rounded-xl border border-slate-800 bg-slate-950 text-cyan-300">{icon}</div><h2 className="text-base font-medium">{title}</h2><p className="mt-2 text-sm text-slate-500">{body}</p></div></div>;
}
