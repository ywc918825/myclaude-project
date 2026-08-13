const BASE = 'http://localhost:4001';

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`core-api ${res.status}: ${text}`);
  }
  return res.status === 204 ? null : res.json();
}

export const coreApi = {
  getCategories: () => request('/api/categories'),
  listProducts: () => request('/api/products'),
  getProduct: (id) => request(`/api/products/${id}`),
  createProduct: (data) => request('/api/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/api/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/api/products/${id}`, { method: 'DELETE' })
};
