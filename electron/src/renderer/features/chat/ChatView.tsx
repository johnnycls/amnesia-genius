import { Bot, CircleStop, MessageSquare, Send } from 'lucide-react';
import type { ReactNode, RefObject } from 'react';
import { EmptyState } from '../../components/EmptyState';
import { IconButton } from '../../components/IconButton';
import { MarkdownContent } from '../../components/MarkdownContent';
import { useI18n } from '../../i18n/i18n';
import type { ChatMessage } from '../../lib/messages';
import { MessageBubble } from './MessageBubble';

export function ChatView({ messages, streamingText, input, setInput, busy, ready, send, cancel, inputRef }: { messages: ChatMessage[]; streamingText: string; input: string; setInput: (value: string) => void; busy: boolean; ready: boolean; send: (text?: string) => void; cancel: () => Promise<void>; inputRef: RefObject<HTMLTextAreaElement | null> }) {
  const { t } = useI18n();
  return <div className="mx-auto flex h-full max-w-5xl flex-col gap-4">
    <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-slate-800 bg-slate-900/40 p-3 sm:p-5">
      {messages.length === 0 && !streamingText ? <EmptyState icon={<MessageSquare size={24} />} title={t('startConversation')} body={t('startConversationHint')} /> : <div className="space-y-5">{messages.map((message) => <MessageBubble key={message.id} message={message} onChoice={(choice) => send(choice)} />)}{streamingText && <AssistantBlock label={`${t('agent')} · ${t('streaming')}`}><MarkdownContent text={streamingText} /></AssistantBlock>}</div>}
    </div>
    <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
      <textarea ref={inputRef} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder={ready ? t('messagePlaceholder') : t('waitingForServer')} disabled={!ready || busy} rows={3} className="w-full resize-none bg-transparent px-2 py-1 text-sm text-slate-100 outline-none placeholder:text-slate-600 disabled:cursor-not-allowed" />
      <div className="flex items-center justify-between border-t border-slate-800 pt-3"><span className="text-[11px] text-slate-600">{t('enterToSend')}</span>{busy ? <IconButton label={t('stop')} onClick={() => void cancel()} className="text-rose-300 hover:bg-rose-950/50"><CircleStop size={16} /></IconButton> : <IconButton label={t('send')} onClick={() => send()} disabled={!ready || !input.trim()} className="bg-cyan-400 text-slate-950 hover:bg-cyan-300"><Send size={16} /></IconButton>}</div>
    </div>
  </div>;
}

function AssistantBlock({ label, children }: { label: string; children: ReactNode }) { return <div className="flex gap-3"><div className="mt-1 grid size-7 shrink-0 place-items-center rounded-md bg-cyan-400/10 text-cyan-300"><Bot size={15} /></div><div className="min-w-0 flex-1 rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-3"><div className="mb-1 text-xs font-medium text-cyan-300">{label}</div>{children}</div></div>; }

