// Relative path, proxied by Vite (see vite.config.js) to reminder-api on
// localhost:4002. See coreApi.js for why this is a same-origin relative path.
const BASE = '/proxy/reminder-api';

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`reminder-api ${res.status}: ${text}`);
  }
  return res.status === 204 ? null : res.json();
}

export const reminderApi = {
  getIngredientRules: () => request('/api/ingredient-rules'),
  checkConflicts: (products) => request('/api/conflict-check', { method: 'POST', body: JSON.stringify({ products }) }),
  getReport: (products) => request('/api/report', { method: 'POST', body: JSON.stringify({ products }) })
};
