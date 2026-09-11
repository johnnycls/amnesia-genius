import { describe, expect, it } from 'vitest';
import { SseParser } from './sse';

describe('SseParser', () => {
  it('parses events split across chunks', () => {
    const parser = new SseParser();
    expect(parser.push('data: {"type":"delta","data":{"text":"hel')).toEqual([]);
    expect(parser.push('lo"}}\n\ndata: {"type":"done","data":{}}\n\n')).toEqual([
      { type: 'delta', data: { text: 'hello' } },
      { type: 'done', data: {} },
    ]);
  });

  it('ignores comments and non-data lines', () => {
    const parser = new SseParser();
    expect(parser.push(': keep-alive\nevent: message\ndata: {"type":"done","data":{}}\n\n')).toEqual([
      { type: 'done', data: {} },
    ]);
  });
});
