import { Bot, Menu, PanelLeft, X } from 'lucide-react';
import { useState, type ReactNode } from 'react';
import type { View, ServerState } from '../../shared/types';
import { ConnectionIndicator } from '../components/ConnectionIndicator';
import { IconButton } from '../components/IconButton';
import { LanguagePicker } from '../components/LanguagePicker';
import { useI18n } from '../i18n/i18n';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { Navigation } from './Navigation';

export function AppShell({ view, setView, server, notice, setNotice, children }: { view: View; setView: (view: View) => void; server: ServerState; notice: string; setNotice: (notice: string) => void; children: ReactNode }) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isNarrow = useMediaQuery('(max-width: 767px)');
  return <div className="flex h-screen min-h-0 bg-slate-950 text-slate-100">
    <aside className={`hidden shrink-0 flex-col border-r border-slate-800 bg-slate-900/80 transition-[width] duration-150 md:flex ${expanded ? 'w-56' : 'w-16'}`}><div className="flex h-16 items-center justify-center border-b border-slate-800 px-3"><div className="grid size-8 shrink-0 place-items-center rounded-lg bg-cyan-400/15 text-cyan-300"><Bot size={19} /></div></div><div className="flex-1"><Navigation view={view} setView={setView} expanded={expanded} /></div><div className="border-t border-slate-800 p-3"><IconButton label={t('toggleSidebar')} onClick={() => setExpanded((value) => !value)} className="w-full text-slate-500 hover:bg-slate-800 hover:text-slate-200"><PanelLeft size={17} /></IconButton></div></aside>
    {isNarrow && mobileOpen && <div className="fixed inset-0 z-40 bg-slate-950/70" onClick={() => setMobileOpen(false)}><aside className="h-full w-64 border-r border-slate-800 bg-slate-900 p-3" onClick={(event) => event.stopPropagation()}><div className="flex h-12 items-center justify-between"><div className="grid size-8 place-items-center rounded-lg bg-cyan-400/15 text-cyan-300"><Bot size={19} /></div><IconButton label={t('closeMenu')} onClick={() => setMobileOpen(false)} className="text-slate-400 hover:bg-slate-800"><X size={17} /></IconButton></div><Navigation view={view} setView={setView} expanded closeMobile={() => setMobileOpen(false)} /></aside></div>}
    <main className="flex min-w-0 flex-1 flex-col"><header className="flex min-h-16 items-center justify-between border-b border-slate-800 px-3 sm:px-6"><div className="flex items-center gap-2">{isNarrow && <IconButton label={t('openMenu')} onClick={() => setMobileOpen(true)} className="text-slate-400 hover:bg-slate-800"><Menu size={18} /></IconButton>}<div className="grid size-8 place-items-center rounded-lg bg-cyan-400/15 text-cyan-300 md:hidden"><Bot size={17} /></div></div><div className="flex items-center gap-1"><ConnectionIndicator state={server} /><LanguagePicker /></div></header>{notice && <div className="flex items-center gap-2 border-b border-cyan-900/50 bg-cyan-950/30 px-4 py-2 text-xs text-cyan-200"><span className="min-w-0 flex-1 truncate">{notice}</span><IconButton label={t('dismiss')} onClick={() => setNotice('')} className="size-7 text-cyan-300 hover:bg-cyan-900/50"><X size={14} /></IconButton></div>}<div className="min-h-0 flex-1 p-3 sm:p-6">{children}</div></main>
  </div>;
}
