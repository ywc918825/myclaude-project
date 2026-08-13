const { test } = require('node:test');
const assert = require('node:assert/strict');
const { addMonths, daysFromToday, statusFromDaysRemaining } = require('../dateUtils');

test('addMonths: plain same-day-of-month add', () => {
  assert.equal(addMonths('2026-08-13', 12), '2027-08-13');
  assert.equal(addMonths('2026-01-05', 6), '2026-07-05');
});

test('addMonths: clamps to month-end instead of overflowing (Jan 31 + 1mo)', () => {
  // Naive Date#setMonth would roll this over to Mar 3 2026 — must clamp to Feb 28 instead.
  assert.equal(addMonths('2026-01-31', 1), '2026-02-28');
});

test('addMonths: clamps into a leap-year February correctly', () => {
  assert.equal(addMonths('2027-01-31', 13), '2028-02-29'); // 2028 is a leap year
});

test('addMonths: crosses a year boundary', () => {
  assert.equal(addMonths('2026-12-15', 6), '2027-06-15');
});

test('daysFromToday: matches known offsets relative to real today', () => {
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  assert.equal(daysFromToday(todayStr), 0);

  const future = new Date(today);
  future.setUTCDate(future.getUTCDate() + 10);
  assert.equal(daysFromToday(future.toISOString().slice(0, 10)), 10);

  const past = new Date(today);
  past.setUTCDate(past.getUTCDate() - 5);
  assert.equal(daysFromToday(past.toISOString().slice(0, 10)), -5);
});

test('statusFromDaysRemaining: boundaries', () => {
  assert.equal(statusFromDaysRemaining(-1), 'expired');
  assert.equal(statusFromDaysRemaining(0), 'warning');
  assert.equal(statusFromDaysRemaining(14), 'warning');
  assert.equal(statusFromDaysRemaining(15), 'ok');
  assert.equal(statusFromDaysRemaining(365), 'ok');
});
