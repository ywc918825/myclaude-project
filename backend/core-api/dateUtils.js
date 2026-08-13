// Add `months` calendar months to a "YYYY-MM-DD" date string, clamping to
// the last day of the target month when the source day doesn't exist there
// (e.g. Jan 31 + 1 month -> Feb 28, not an overflowed Mar 3).
function addMonths(dateStr, months) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const targetIndex = (m - 1) + months;
  const targetYear = y + Math.floor(targetIndex / 12);
  const targetMonth = ((targetIndex % 12) + 12) % 12;
  const lastDayOfTargetMonth = new Date(Date.UTC(targetYear, targetMonth + 1, 0)).getUTCDate();
  const clampedDay = Math.min(d, lastDayOfTargetMonth);
  return new Date(Date.UTC(targetYear, targetMonth, clampedDay)).toISOString().slice(0, 10);
}

// Integer day difference from today (UTC midnight) to target "YYYY-MM-DD" date.
function daysFromToday(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const target = Date.UTC(y, m - 1, d);

  const now = new Date();
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());

  const MS_PER_DAY = 24 * 60 * 60 * 1000;
  return Math.round((target - today) / MS_PER_DAY);
}

function statusFromDaysRemaining(daysRemaining) {
  if (daysRemaining < 0) return 'expired';
  if (daysRemaining <= 14) return 'warning';
  return 'ok';
}

module.exports = { addMonths, daysFromToday, statusFromDaysRemaining };
