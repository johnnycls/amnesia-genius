import { FileText, History, MessageSquare, Settings } from 'lucide-react';
import type { View } from '../../shared/types';
import { IconButton } from '../components/IconButton';
import { useI18n } from '../i18n/i18n';

const items: Array<{ id: View; label: string; icon: typeof MessageSquare }> = [
  { id: 'chat', label: 'chat', icon: MessageSquare }, { id: 'workspace', label: 'workspace', icon: FileText }, { id: 'history', label: 'history', icon: History }, { id: 'settings', label: 'settings', icon: Settings },
];

export function Navigation({ view, setView, expanded, closeMobile }: { view: View; setView: (view: View) => void; expanded: boolean; closeMobile?: () => void }) {
  const { t } = useI18n();
  return <nav className="space-y-1 p-3">{items.map(({ id, label, icon: Icon }) => <IconButton key={id} label={t(label)} onClick={() => { setView(id); closeMobile?.(); }} className={`flex w-full items-center gap-3 px-3 text-left ${view === id ? 'bg-slate-800 text-cyan-300' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100'} ${expanded ? 'justify-start' : 'justify-center'}`}><Icon size={17} /></IconButton>)}</nav>;
}
