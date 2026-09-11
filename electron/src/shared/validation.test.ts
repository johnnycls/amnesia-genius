import { describe, expect, it } from 'vitest';
import { parsePositiveInteger, parsePositiveNumber, parseProviderParams } from './validation';

describe('settings validation', () => {
  it('accepts a JSON object', () => {
    expect(parseProviderParams('{"temperature":0.2}')).toEqual({ temperature: 0.2 });
  });

  it('rejects invalid provider params', () => {
    expect(() => parseProviderParams('[]')).toThrow('JSON object');
    expect(() => parseProviderParams('{')).toThrow('valid JSON');
  });

  it('validates numeric limits', () => {
    expect(parsePositiveNumber('2.5', 'Timeout')).toBe(2.5);
    expect(parsePositiveInteger('128', 'Output')).toBe(128);
    expect(() => parsePositiveNumber('0', 'Timeout')).toThrow('positive');
    expect(() => parsePositiveInteger('1.5', 'Output')).toThrow('integer');
  });
});
