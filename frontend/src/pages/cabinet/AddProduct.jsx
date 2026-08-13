import React, { useEffect, useState } from 'react';
import { coreApi } from '../../api/coreApi.js';

const PAO_OPTIONS = [6, 12, 18, 24];

const INGREDIENT_VOCAB = [
  '维生素C',
  '烟酰胺',
  '视黄醇(A醇)',
  '水杨酸',
  '果酸(AHA)',
  '苯氧乙醇',
  '尿素',
  '神经酰胺',
  '玻尿酸',
  '积雪草',
  '熊果苷',
  '传明酸',
  '二裂酵母',
  '维生素E',
  '甘草酸二钾'
];

function todayStr() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const initialForm = {
  name: '',
  brand: '',
  category: '',
  openedDate: todayStr(),
  paoMonths: 12,
  ingredientTags: [],
  costCNY: ''
};

// STUB — implemented by frontend workflow A per DESIGN.md contract.
// Props: { onCreated: () => void }
export default function AddProduct({ onCreated }) {
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    coreApi
      .getCategories()
      .then((cats) => {
        if (cancelled) return;
        setCategories(cats);
        setForm((f) => (f.category ? f : { ...f, category: cats[0] || '' }));
      })
      .catch((err) => {
        if (!cancelled) setError(`获取分类失败：${err.message}`);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const updateField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const toggleIngredient = (tag) => {
    setForm((f) => {
      const has = f.ingredientTags.includes(tag);
      return {
        ...f,
        ingredientTags: has
          ? f.ingredientTags.filter((t) => t !== tag)
          : [...f.ingredientTags, tag]
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.name.trim()) {
      setError('请填写产品名称');
      return;
    }
    if (!form.category) {
      setError('请选择分类');
      return;
    }

    setSubmitting(true);
    try {
      await coreApi.createProduct({
        name: form.name.trim(),
        brand: form.brand.trim(),
        category: form.category,
        openedDate: form.openedDate,
        paoMonths: Number(form.paoMonths),
        ingredientTags: form.ingredientTags,
        costCNY: form.costCNY === '' ? 0 : Number(form.costCNY),
        photoUrl: null
      });
      setForm({ ...initialForm, category: categories[0] || '' });
      onCreated && onCreated();
    } catch (err) {
      setError(`创建失败：${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="section-title">添加产品</div>

      {error && (
        <div className="status-expired" style={{ marginBottom: 12, fontSize: 13 }}>
          {error}
        </div>
      )}

      <div className="field">
        <label htmlFor="name">产品名称</label>
        <input
          id="name"
          type="text"
          value={form.name}
          onChange={(e) => updateField('name', e.target.value)}
          placeholder="例如：温和洁面乳"
        />
      </div>

      <div className="field">
        <label htmlFor="brand">品牌</label>
        <input
          id="brand"
          type="text"
          value={form.brand}
          onChange={(e) => updateField('brand', e.target.value)}
          placeholder="例如：珂润"
        />
      </div>

      <div className="field">
        <label htmlFor="category">分类</label>
        <select
          id="category"
          value={form.category}
          onChange={(e) => updateField('category', e.target.value)}
        >
          {categories.length === 0 && <option value="">加载中…</option>}
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="openedDate">开封日期</label>
        <input
          id="openedDate"
          type="date"
          value={form.openedDate}
          onChange={(e) => updateField('openedDate', e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="paoMonths">开封后有效期（月）</label>
        <select
          id="paoMonths"
          value={form.paoMonths}
          onChange={(e) => updateField('paoMonths', e.target.value)}
        >
          {PAO_OPTIONS.map((m) => (
            <option key={m} value={m}>
              {m} 个月
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label>成分标签</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {INGREDIENT_VOCAB.map((tag) => (
            <label
              key={tag}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: 13,
                background: form.ingredientTags.includes(tag) ? 'var(--pink-100)' : 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 999,
                padding: '4px 10px',
                cursor: 'pointer'
              }}
            >
              <input
                type="checkbox"
                checked={form.ingredientTags.includes(tag)}
                onChange={() => toggleIngredient(tag)}
                style={{ margin: 0 }}
              />
              {tag}
            </label>
          ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="costCNY">价格（元）</label>
        <input
          id="costCNY"
          type="number"
          min="0"
          step="0.01"
          value={form.costCNY}
          onChange={(e) => updateField('costCNY', e.target.value)}
          placeholder="0"
        />
      </div>

      <button type="submit" className="btn-primary" disabled={submitting}>
        {submitting ? '保存中…' : '保存产品'}
      </button>
    </form>
  );
}
