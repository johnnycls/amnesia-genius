export function parseProviderParams(value: string, invalidMessage: string): Record<string, unknown> {
  let parsed: unknown;
  try { parsed = JSON.parse(value); } catch { throw new Error(invalidMessage); }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error(invalidMessage);
  return parsed as Record<string, unknown>;
}
export function parsePositiveNumber(value: string, message: string): number { const parsed = Number(value); if (!Number.isFinite(parsed) || parsed <= 0) throw new Error(message); return parsed; }
export function parsePositiveInteger(value: string, message: string): number { const parsed = Number(value); if (!Number.isInteger(parsed) || parsed <= 0) throw new Error(message); return parsed; }
