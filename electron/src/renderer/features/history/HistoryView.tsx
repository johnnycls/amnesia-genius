import { Clock3, History, Trash2 } from 'lucide-react';
import { useMemo } from 'react';
import { EmptyState } from '../../components/EmptyState';
import { IconButton } from '../../components/IconButton';
import { useI18n } from '../../i18n/i18n';
import { historyToMessages } from '../../lib/messages';
import { MessageBubble } from '../chat/MessageBubble';
import type { HistoryRecord } from '../../../shared/types';

export function HistoryView({ dates, selectedDate, records, loadHistory, resetHistory }: { dates: string[]; selectedDate: string; records: HistoryRecord[]; loadHistory: (date: string) => Promise<void>; resetHistory: () => Promise<void> }) {
  const { t } = useI18n();
  const formatted = useMemo(() => historyToMessages(records), [records]);
  return <div className="mx-auto grid h-full max-w-6xl min-h-0 grid-cols-1 gap-5 lg:grid-cols-[15rem_1fr]"><section className="flex min-h-0 max-h-44 flex-col rounded-lg border border-slate-800 bg-slate-900/50 p-4 lg:max-h-none"><div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-medium">{t('savedDays')}</h2><IconButton label={t('clearHistory')} onClick={() => void resetHistory()} className="text-slate-500 hover:bg-rose-950/50 hover:text-rose-300"><Trash2 size={14} /></IconButton></div>{dates.length === 0 ? <p className="text-xs text-slate-600">{t('noHistory')}</p> : <div className="flex gap-1 overflow-x-auto pb-1 lg:block lg:space-y-1 lg:overflow-y-auto">{dates.map((date) => <button key={date} onClick={() => void loadHistory(date)} className={`flex shrink-0 items-center gap-2 rounded px-2 py-2 text-left text-xs ${selectedDate === date ? 'bg-slate-800 text-cyan-300' : 'text-slate-400 hover:bg-slate-800/60'}`}><Clock3 size={13} />{date}</button>)}</div>}</section><section className="min-h-0 overflow-y-auto rounded-lg border border-slate-800 bg-slate-900/40 p-4 sm:p-5">{selectedDate ? <><div className="mb-5 flex items-center justify-between border-b border-slate-800 pb-4"><div><h2 className="font-medium">{selectedDate}</h2><p className="mt-1 text-xs text-slate-500">{t('readOnlyHistory')}</p></div><History size={18} className="text-slate-600" /></div><div className="space-y-5">{formatted.length ? formatted.map((message) => <MessageBubble key={message.id} message={message} onChoice={() => undefined} />) : <p className="text-sm text-slate-500">{t('noHistory')}</p>}</div></> : <EmptyState icon={<History size={24} />} title={t('chooseSavedDay')} body={t('historyHint')} />}</section></div>;
}
