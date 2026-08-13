const BASE = 'http://localhost:4002';

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
