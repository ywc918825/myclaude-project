import React, { useEffect, useState } from 'react';
import { coreApi } from '../../api/coreApi.js';

const STATUS_VAR = {
  ok: 'var(--ok)',
  warning: 'var(--warning)',
  expired: 'var(--expired)'
};

const STATUS_CLASS = {
  ok: 'status-ok',
  warning: 'status-warning',
  expired: 'status-expired'
};

function daysRemainingText(daysRemaining) {
  if (daysRemaining < 0) {
    return `已过期${Math.abs(daysRemaining)}天`;
  }
  return `还有${daysRemaining}天到期`;
}

function progressPercent(product) {
  const opened = new Date(product.openedDate);
  const expiry = new Date(product.expiryDate);
  const today = new Date();
  const totalMs = expiry - opened;
  if (!totalMs || totalMs <= 0) return 100;
  const elapsedMs = today - opened;
  const pct = (elapsedMs / totalMs) * 100;
  return Math.min(100, Math.max(0, pct));
}

// STUB — implemented by frontend workflow A per DESIGN.md contract.
// Props: { refreshKey: number }
export default function CabinetOverview({ refreshKey }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState('全部');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    coreApi
      .getCategories()
      .then(setCategories)
      .catch(() => {
        /* category filter row falls back to whatever we already have */
      });
  }, []);

  const loadProducts = () => {
    setLoading(true);
    setError('');
    coreApi
      .listProducts()
      .then((list) => {
        setProducts(list);
      })
      .catch((err) => {
        setError(`加载失败：${err.message}`);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const handleDelete = async (id) => {
    try {
      await coreApi.deleteProduct(id);
      loadProducts();
    } catch (err) {
      setError(`删除失败：${err.message}`);
    }
  };

  const filtered = (activeCategory === '全部'
    ? products
    : products.filter((p) => p.category === activeCategory)
  )
    .slice()
    .sort((a, b) => a.daysRemaining - b.daysRemaining);

  return (
    <div>
      <div className="section-title">我的梳妆台</div>

      {error && (
        <div className="status-expired" style={{ marginBottom: 12, fontSize: 13 }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: 16 }}>
        {['全部', ...categories].map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            style={{
              border: '1px solid var(--border)',
              borderRadius: 999,
              padding: '6px 14px',
              fontSize: 13,
              cursor: 'pointer',
              background: activeCategory === cat ? 'var(--pink-500)' : 'white',
              color: activeCategory === cat ? 'white' : 'var(--ink)'
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {!loading && filtered.length === 0 && (
        <div className="empty-state">还没有产品，快去添加一个吧～</div>
      )}

      {filtered.map((product) => (
        <div className="card" key={product.id}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600 }}>{product.name}</div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>{product.brand}</div>
            </div>
            <span className="badge">{product.category}</span>
          </div>

          <div style={{ margin: '10px 0 6px' }}>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{
                  width: `${progressPercent(product)}%`,
                  backgroundColor: STATUS_VAR[product.status] || 'var(--ok)'
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className={STATUS_CLASS[product.status] || 'status-ok'} style={{ fontSize: 13 }}>
              {daysRemainingText(product.daysRemaining)}
            </span>
            <button
              type="button"
              onClick={() => handleDelete(product.id)}
              style={{
                border: 'none',
                background: 'none',
                color: 'var(--muted)',
                fontSize: 13,
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              删除
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
