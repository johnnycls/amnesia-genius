import type { HistoryRecord } from '../../shared/types';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool_call' | 'tool_result' | 'error';
  text: string;
  choices?: string[];
  data?: Record<string, unknown>;
}

export function uid(): string { return `${Date.now()}-${Math.random().toString(36).slice(2)}`; }

export function readAssistantContent(content: string): { text: string; choices: string[] } {
  try {
    const parsed: unknown = JSON.parse(content);
    if (parsed && typeof parsed === 'object' && typeof (parsed as { answer?: unknown }).answer === 'string' && Array.isArray((parsed as { choices?: unknown }).choices)) {
      return { text: (parsed as { answer: string }).answer, choices: (parsed as { choices: unknown[] }).choices.filter((choice): choice is string => typeof choice === 'string') };
    }
  } catch { /* Plain text history is valid. */ }
  return { text: content, choices: [] };
}

export function historyToMessages(records: HistoryRecord[]): ChatMessage[] {
  return records.flatMap<ChatMessage>((record) => {
    const content = typeof record.content === 'string' ? record.content : '';
    if (record.role === 'user') return [{ id: uid(), role: 'user', text: content }];
    if (record.role === 'assistant') { const answer = readAssistantContent(content); return [{ id: uid(), role: 'assistant', text: answer.text, choices: answer.choices }]; }
    if (record.role === 'tool') return [{ id: uid(), role: 'tool_result', text: content }];
    return [];
  });
}
