import { describe, it, expect } from 'vitest';
import { daysRemainingText, progressPercent } from './CabinetOverview.jsx';

describe('daysRemainingText', () => {
  it('formats a future expiry as "还有N天到期"', () => {
    expect(daysRemainingText(12)).toBe('还有12天到期');
  });

  it('formats zero days remaining the same as a positive count', () => {
    expect(daysRemainingText(0)).toBe('还有0天到期');
  });

  it('formats overdue products as "已过期N天"', () => {
    expect(daysRemainingText(-5)).toBe('已过期5天');
  });
});

describe('progressPercent', () => {
  it('clamps to 100 once past the expiry date', () => {
    const product = { openedDate: '2020-01-01', expiryDate: '2020-02-01' };
    expect(progressPercent(product)).toBe(100);
  });

  it('is 0 right at the opened date', () => {
    const today = new Date().toISOString().slice(0, 10);
    const future = new Date();
    future.setFullYear(future.getFullYear() + 1);
    const product = { openedDate: today, expiryDate: future.toISOString().slice(0, 10) };
    expect(progressPercent(product)).toBeCloseTo(0, 0);
  });

  it('never returns a value outside [0, 100]', () => {
    const product = { openedDate: '2099-01-01', expiryDate: '2099-02-01' }; // opened in the future
    const pct = progressPercent(product);
    expect(pct).toBeGreaterThanOrEqual(0);
    expect(pct).toBeLessThanOrEqual(100);
  });
});
