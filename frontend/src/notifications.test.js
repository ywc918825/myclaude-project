import { describe, it, expect } from 'vitest';
import { shouldNotifyToday, buildNotificationBody } from './notifications.js';

describe('shouldNotifyToday', () => {
  it('is true the first time (no prior notified date)', () => {
    expect(shouldNotifyToday(null, '2026-08-13')).toBe(true);
    expect(shouldNotifyToday(undefined, '2026-08-13')).toBe(true);
  });

  it('is false once already notified today', () => {
    expect(shouldNotifyToday('2026-08-13', '2026-08-13')).toBe(false);
  });

  it('is true again on a new day', () => {
    expect(shouldNotifyToday('2026-08-12', '2026-08-13')).toBe(true);
  });
});

describe('buildNotificationBody', () => {
  it('includes the count of products needing attention', () => {
    expect(buildNotificationBody(3)).toContain('3');
  });
});
