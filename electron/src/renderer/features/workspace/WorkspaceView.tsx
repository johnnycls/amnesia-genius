import { RefreshCw, Save } from 'lucide-react';
import { useI18n } from '../../i18n/i18n';
import { IconButton } from '../../components/IconButton';

export function WorkspaceView({ systemPrompt, memory, setSystemPrompt, setMemory, saveContent, resetContent, busy }: { systemPrompt: string; memory: string; setSystemPrompt: (value: string) => void; setMemory: (value: string) => void; saveContent: (path: string, content: string, label: string) => Promise<void>; resetContent: (path: string, setter: (content: string) => void, label: string) => Promise<void>; busy: boolean }) {
  const { t } = useI18n();
  return <div className="mx-auto grid h-full max-w-6xl min-h-0 grid-cols-1 gap-5 overflow-y-auto lg:grid-cols-2"><EditorCard title={t('systemPrompt')} description={t('systemPromptHint')} value={systemPrompt} setValue={setSystemPrompt} save={() => saveContent('/v1/workspace/system-prompt', systemPrompt, t('systemPrompt'))} reset={() => resetContent('/v1/workspace/system-prompt/reset', setSystemPrompt, t('systemPrompt'))} busy={busy} /><EditorCard title={t('memory')} description={t('memoryHint')} value={memory} setValue={setMemory} save={() => saveContent('/v1/workspace/memory', memory, t('memory'))} reset={() => resetContent('/v1/workspace/memory/reset', setMemory, t('memory'))} busy={busy} /></div>;
}

function EditorCard({ title, description, value, setValue, save, reset, busy }: { title: string; description: string; value: string; setValue: (value: string) => void; save: () => Promise<void>; reset: () => Promise<void>; busy: boolean }) {
  const { t } = useI18n();
  return <section className="flex min-h-[28rem] flex-col rounded-lg border border-slate-800 bg-slate-900/50 p-4 sm:p-5"><div className="mb-4"><h2 className="font-medium">{title}</h2><p className="mt-1 text-xs text-slate-500">{description}</p></div><textarea aria-label={title} value={value} onChange={(event) => setValue(event.target.value)} className="min-h-0 flex-1 resize-none rounded-md border border-slate-800 bg-slate-950/70 p-3 font-mono text-xs leading-5 text-slate-300 outline-none focus:border-cyan-700" /><div className="mt-4 flex justify-end gap-1"><IconButton label={t('save')} onClick={() => void save()} disabled={busy} className="text-cyan-300 hover:bg-cyan-950/50"><Save size={16} /></IconButton><IconButton label={t('reset')} onClick={() => void reset()} disabled={busy} className="text-slate-400 hover:bg-slate-800"><RefreshCw size={16} /></IconButton></div></section>;
}
