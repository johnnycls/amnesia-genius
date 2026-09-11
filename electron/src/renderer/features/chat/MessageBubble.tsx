import { Bot, CircleAlert, Code2, Terminal } from 'lucide-react';
import { useI18n } from '../../i18n/i18n';
import { MarkdownContent } from '../../components/MarkdownContent';
import type { ChatMessage } from '../../lib/messages';

export function MessageBubble({ message, onChoice }: { message: ChatMessage; onChoice: (choice: string) => void }) {
  const { t } = useI18n();
  if (message.role === 'user') return <div className="flex justify-end"><div className="max-w-[90%] rounded-lg bg-cyan-400 px-4 py-3 text-sm text-slate-950 sm:max-w-[80%]"><div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-700">{t('you')}</div><div className="whitespace-pre-wrap">{message.text}</div></div></div>;
  if (message.role === 'error') return <div className="flex gap-3 rounded-lg border border-rose-900/70 bg-rose-950/20 p-3 text-sm text-rose-200"><CircleAlert size={16} className="mt-0.5 shrink-0" /><span>{message.text}</span></div>;
  if (message.role === 'tool_call') return <div className="flex items-center gap-2 text-xs text-slate-500"><Terminal size={14} /><span>{t('toolCall')}</span><span aria-hidden>›</span></div>;
  if (message.role === 'tool_result') return <details className="rounded-md border border-slate-800 bg-slate-950/50 p-3 text-xs text-slate-400"><summary className="cursor-pointer list-none font-medium text-slate-400"><span className="inline-flex items-center gap-2"><Code2 size={14} />{t('toolResult')}</span></summary><pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap">{message.text}</pre></details>;
  return <div className="flex gap-3"><div className="mt-1 grid size-7 shrink-0 place-items-center rounded-md bg-cyan-400/10 text-cyan-300"><Bot size={15} /></div><div className="min-w-0 flex-1"><div className="mb-1 text-xs font-medium text-cyan-300">{t('agent')}</div><MarkdownContent text={message.text} />{message.choices && message.choices.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{message.choices.map((choice) => <button key={choice} onClick={() => onChoice(choice)} className="rounded-md border border-cyan-800 px-3 py-1.5 text-xs text-cyan-300 hover:bg-cyan-950/50">{choice}</button>)}</div>}</div></div>;
}
