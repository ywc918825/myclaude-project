import { describe, it, expect } from 'vitest';
import { normalizeMonthly, formatCNY } from './ConsumptionReport.jsx';

describe('formatCNY', () => {
  it('formats a plain number with a yen sign, rounded', () => {
    expect(formatCNY(129)).toBe('¥129');
    expect(formatCNY(129.6)).toBe('¥130');
  });

  it('treats non-numeric input as 0', () => {
    expect(formatCNY(undefined)).toBe('¥0');
    expect(formatCNY('not-a-number')).toBe('¥0');
  });
});

describe('normalizeMonthly', () => {
  it('passes through the flattened {month,count,costCNY}[] shape core-api/reminder-api actually return, sorted', () => {
    const input = [
      { month: '2026-03', count: 1, costCNY: 10 },
      { month: '2026-01', count: 2, costCNY: 25 }
    ];
    expect(normalizeMonthly(input)).toEqual([
      { month: '2026-01', count: 2, costCNY: 25 },
      { month: '2026-03', count: 1, costCNY: 10 }
    ]);
  });

  it('returns an empty array for null/undefined input', () => {
    expect(normalizeMonthly(null)).toEqual([]);
    expect(normalizeMonthly(undefined)).toEqual([]);
  });

  it('also tolerates a plain object-map shape defensively', () => {
    const input = { '2026-02': { count: 1, costCNY: 5 } };
    expect(normalizeMonthly(input)).toEqual([{ month: '2026-02', count: 1, costCNY: 5 }]);
  });
});
