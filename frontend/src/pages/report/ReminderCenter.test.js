import { describe, it, expect } from 'vitest';
import { daysRemainingText } from './ReminderCenter.jsx';

describe('daysRemainingText (reminder center wording)', () => {
  it('formats an active warning as "剩余N天"', () => {
    expect(daysRemainingText({ status: 'warning', daysRemaining: 3 })).toBe('剩余 3 天');
  });

  it('formats an expired product with a day count as "已过期N天"', () => {
    expect(daysRemainingText({ status: 'expired', daysRemaining: -7 })).toBe('已过期 7 天');
  });

  it('falls back to a bare "已过期" when daysRemaining is exactly 0 but flagged expired', () => {
    expect(daysRemainingText({ status: 'expired', daysRemaining: 0 })).toBe('已过期');
  });
});
