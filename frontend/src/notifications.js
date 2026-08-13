const LAST_NOTIFIED_KEY = 'reminderLastNotifiedDate';
const ENABLED_KEY = 'reminderNotificationsEnabled';

export function todayDateStr() {
  return new Date().toISOString().slice(0, 10);
}

// Only notify once per calendar day, even though this page can be revisited
// many times — otherwise every tab switch would re-fire the same alert.
export function shouldNotifyToday(lastNotifiedDate, today = todayDateStr()) {
  return lastNotifiedDate !== today;
}

export function buildNotificationBody(count) {
  return `你有 ${count} 件产品需要关注：即将到期或已过期，打开梳妆台管家查看详情。`;
}

export function isNotificationsEnabled() {
  return typeof localStorage !== 'undefined' && localStorage.getItem(ENABLED_KEY) === 'true';
}

export function setNotificationsEnabled(enabled) {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(ENABLED_KEY, enabled ? 'true' : 'false');
}

export function getLastNotifiedDate() {
  return typeof localStorage !== 'undefined' ? localStorage.getItem(LAST_NOTIFIED_KEY) : null;
}

export function setLastNotifiedDate(dateStr) {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(LAST_NOTIFIED_KEY, dateStr);
}

// Fires a browser Notification for `count` products needing attention, at
// most once per day. Caller is responsible for checking Notification
// permission/support first. This only fires while the page is open — it is
// not a real background push (that would need a service worker + push
// server, out of scope for this prototype).
export function maybeNotify(count) {
  if (count <= 0) return false;
  if (!shouldNotifyToday(getLastNotifiedDate())) return false;

  new Notification('梳妆台管家', { body: buildNotificationBody(count) });
  setLastNotifiedDate(todayDateStr());
  return true;
}
