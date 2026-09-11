import type { ServerEvent } from './types.js';

export class SseParser {
  private buffer = '';

  push(chunk: string): ServerEvent[] {
    this.buffer += chunk;
    const events: ServerEvent[] = [];
    const parts = this.buffer.split(/\r?\n\r?\n/);
    this.buffer = parts.pop() ?? '';
    for (const part of parts) {
      const data = part
        .split(/\r?\n/)
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).trimStart())
        .join('\n');
      if (!data) continue;
      const parsed: unknown = JSON.parse(data);
      if (isServerEvent(parsed)) events.push(parsed);
    }
    return events;
  }

  finish(): ServerEvent[] {
    const remainder = this.buffer;
    this.buffer = '';
    if (!remainder.trim()) return [];
    const data = remainder
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n');
    if (!data) return [];
    const parsed: unknown = JSON.parse(data);
    return isServerEvent(parsed) ? [parsed] : [];
  }
}

function isServerEvent(value: unknown): value is ServerEvent {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as { type?: unknown; data?: unknown };
  return typeof candidate.type === 'string' && !!candidate.data && typeof candidate.data === 'object';
}
