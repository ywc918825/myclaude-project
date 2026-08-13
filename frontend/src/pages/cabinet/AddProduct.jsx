import React, { useEffect, useRef, useState } from 'react';
import { coreApi, resolveUploadUrl } from '../../api/coreApi.js';
import { searchOpenBeautyFacts, matchKnownIngredients } from '../../api/openBeautyFacts.js';

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

// Downscale a captured photo before OCR/upload — phone camera photos can be
// several MB, which is slow to run OCR on and needlessly large to store.
// maxDim defaults fairly high (vs. a typical thumbnail size) because OCR
// accuracy on small printed ingredient-list text drops off fast once the
// text itself shrinks below a few pixels tall.
function resizeImageToDataUrl(file, maxDim = 2000) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('读取图片失败'));
    reader.onload = () => {
      img.onerror = () => reject(new Error('解析图片失败'));
      img.onload = () => {
        const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL('image/jpeg', 0.85));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

// Symbols that essentially never appear in a real product name but show up
// constantly in OCR misreads of stylized logos/cursive labels/reflections —
// lines containing them are almost certainly noise, not a product name.
const OCR_NOISE_CHARS = /[=:><\\|{}[\]~^`：《》『』""'']/;

// OCR gives us a blob of raw text with no notion of "this is the product
// name" — as a simple stand-in, guess the name is the longest line that (a)
// isn't dominated by digits/punctuation, (b) doesn't contain characters that
// only ever show up as recognition noise, and (c) is long enough to plausibly
// be a name rather than a 1-2 character misread fragment. This filters out
// the worst garbage but can't catch every misread (e.g. real letters that
// spell nonsense) — it's a starting point for the user to correct via the
// "查看识别到的文字" raw text, not a claim of accuracy. Recognition quality
// depends heavily on photo quality: flat printed text (like an ingredients
// list) reads far better than a curved bottle or a cursive brand logo.
export function guessNameFromText(text) {
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.replace(/[\s\d.,:;!?%()-]/g, '').length >= 2)
    .filter((l) => !OCR_NOISE_CHARS.test(l))
    // Chinese product names can legitimately be very short ("水乳", "面霜"),
    // but a short ALL-Latin fragment ("a LL") is almost always a misread —
    // so only Latin/digit-only lines need to clear a higher length bar.
    .filter((l) => (/[一-鿿]/.test(l) ? l.length >= 2 : l.length >= 5))
    .filter((l) => {
      const wordChars = (l.match(/[\p{L}\p{N}]/gu) || []).length;
      return wordChars / l.length >= 0.7;
    });
  if (lines.length === 0) return '';
  return lines.reduce((longest, l) => (l.length > longest.length ? l : longest), lines[0]);
}

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

function productToForm(product) {
  return {
    name: product.name || '',
    brand: product.brand || '',
    category: product.category || '',
    openedDate: product.openedDate || todayStr(),
    paoMonths: product.paoMonths || 12,
    ingredientTags: Array.isArray(product.ingredientTags) ? product.ingredientTags : [],
    costCNY: product.costCNY != null ? String(product.costCNY) : ''
  };
}

// Props: { editingProduct?: Product, onSaved: () => void, onCancel?: () => void }
// Pass a `key` tied to editingProduct?.id from the parent so this component
// remounts (and re-derives its initial state) whenever the edit target changes.
export default function AddProduct({ editingProduct, onSaved, onCancel }) {
  const isEditMode = Boolean(editingProduct);

  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(() => (editingProduct ? productToForm(editingProduct) : initialForm));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fileInputRef = useRef(null);
  // local dataURL for a freshly-picked photo, or the resolved URL of the
  // product's existing photo when opening in edit mode
  const [photoPreview, setPhotoPreview] = useState(() =>
    editingProduct?.photoUrl ? resolveUploadUrl(editingProduct.photoUrl) : null
  );
  const [photoUrl, setPhotoUrl] = useState(() => editingProduct?.photoUrl || null); // uploaded server URL, saved with the product
  const [photoUploading, setPhotoUploading] = useState(false);
  const [ocrStatus, setOcrStatus] = useState('idle'); // idle | recognizing | done | error
  const [ocrProgress, setOcrProgress] = useState(0);
  const [recognizedText, setRecognizedText] = useState('');

  const [lookupStatus, setLookupStatus] = useState('idle'); // idle | searching | results | empty | error
  const [lookupResults, setLookupResults] = useState([]);
  const [lookupError, setLookupError] = useState('');
  const [appliedResult, setAppliedResult] = useState(null); // { name, ingredientsText, matchedTags }

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

  const handlePhotoSelected = async (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = ''; // allow re-selecting the same file later
    if (!file) return;

    setError('');
    setOcrStatus('idle');
    setOcrProgress(0);
    setRecognizedText('');
    setPhotoUrl(null);

    let dataUrl;
    try {
      dataUrl = await resizeImageToDataUrl(file);
    } catch (err) {
      setError(`处理照片失败：${err.message}`);
      return;
    }
    setPhotoPreview(dataUrl);

    // Upload and OCR run independently — a slow/failed OCR shouldn't block
    // the photo from being attached to the product.
    setPhotoUploading(true);
    coreApi
      .uploadImage(dataUrl)
      .then((res) => setPhotoUrl(res.url))
      .catch((err) => setError(`照片上传失败：${err.message}`))
      .finally(() => setPhotoUploading(false));

    setOcrStatus('recognizing');
    try {
      const { createWorker } = await import('tesseract.js');
      const worker = await createWorker('chi_sim+eng', 1, {
        workerPath: '/tesseract-assets/worker.min.js',
        corePath: '/tesseract-assets/',
        langPath: '/tesseract-assets/',
        logger: (m) => {
          if (m.status === 'recognizing text') {
            setOcrProgress(Math.round(m.progress * 100));
          }
        }
      });
      const { data } = await worker.recognize(dataUrl);
      await worker.terminate();

      setRecognizedText(data.text.trim());
      setOcrStatus('done');

      const guessedName = guessNameFromText(data.text);
      if (guessedName) {
        setForm((f) => (f.name.trim() ? f : { ...f, name: guessedName }));
      }
    } catch (err) {
      setOcrStatus('error');
      setError(`识别失败：${err.message}（可以手动填写产品信息）`);
    }
  };

  const handleClearPhoto = () => {
    setPhotoPreview(null);
    setPhotoUrl(null);
    setOcrStatus('idle');
    setOcrProgress(0);
    setRecognizedText('');
  };

  const handleLookup = async () => {
    const query = [form.brand.trim(), form.name.trim()].filter(Boolean).join(' ');
    if (!query) return;

    setLookupStatus('searching');
    setLookupError('');
    setLookupResults([]);
    setAppliedResult(null);

    try {
      const results = await searchOpenBeautyFacts(query);
      setLookupResults(results);
      setLookupStatus(results.length ? 'results' : 'empty');
    } catch (err) {
      setLookupStatus('error');
      // A bare "Failed to fetch" almost always means the request never left
      // the browser (DNS/network/firewall), not that the API responded with
      // an error — Open Beauty Facts is hosted outside mainland China, so
      // this is the most common cause for users without direct access to it.
      setLookupError(
        err.message === 'Failed to fetch'
          ? '连接不上 Open Beauty Facts（world.openbeautyfacts.org）。这个网站在境内可能需要科学上网才能访问，可以在手机浏览器里直接打开这个网址确认是否能连通；连不上的话可以先手动填写产品信息。'
          : err.message
      );
    }
  };

  const handleApplyResult = (product) => {
    const matchedTags = matchKnownIngredients(product.ingredients_text, product.ingredients_text_zh, INGREDIENT_VOCAB);

    setForm((f) => ({
      ...f,
      brand: f.brand.trim() ? f.brand : product.brands || f.brand,
      ingredientTags: Array.from(new Set([...f.ingredientTags, ...matchedTags]))
    }));

    setAppliedResult({
      name: product.product_name,
      ingredientsText: product.ingredients_text_zh || product.ingredients_text || '',
      matchedTags
    });
    setLookupStatus('idle');
    setLookupResults([]);
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

    const payload = {
      name: form.name.trim(),
      brand: form.brand.trim(),
      category: form.category,
      openedDate: form.openedDate,
      paoMonths: Number(form.paoMonths),
      ingredientTags: form.ingredientTags,
      costCNY: form.costCNY === '' ? 0 : Number(form.costCNY),
      photoUrl
    };

    setSubmitting(true);
    try {
      if (isEditMode) {
        await coreApi.updateProduct(editingProduct.id, payload);
      } else {
        await coreApi.createProduct(payload);
        setForm({ ...initialForm, category: categories[0] || '' });
        handleClearPhoto();
        setLookupStatus('idle');
        setLookupResults([]);
        setAppliedResult(null);
      }
      onSaved && onSaved();
    } catch (err) {
      setError(`${isEditMode ? '保存修改' : '创建'}失败：${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="section-title">{isEditMode ? '编辑产品' : '添加产品'}</div>
        {isEditMode && (
          <button
            type="button"
            onClick={() => onCancel && onCancel()}
            style={{ border: 'none', background: 'none', color: 'var(--muted)', fontSize: 13, cursor: 'pointer', textDecoration: 'underline' }}
          >
            取消
          </button>
        )}
      </div>

      {error && (
        <div className="status-expired" style={{ marginBottom: 12, fontSize: 13 }}>
          {error}
        </div>
      )}

      <div className="field">
        <label>拍照识别（可选）</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handlePhotoSelected}
          style={{ display: 'none' }}
        />

        {!photoPreview && (
          <>
            <button
              type="button"
              className="btn-primary"
              style={{ background: 'white', color: 'var(--pink-500)', border: '1px solid var(--pink-400)' }}
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
            >
              📷 拍照 / 上传产品照片
            </button>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 6 }}>
              拍摄小贴士：正对文字、光线充足、离近一点让文字占满画面，识别效果会好很多；瓶身曲面反光的艺术字logo通常很难识别准确，尽量拍外包装上的印刷文字（比如成分表）。
            </div>
          </>
        )}

        {photoPreview && (
          <div className="card" style={{ padding: 10 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <img
                src={photoPreview}
                alt="产品照片预览"
                style={{ width: 84, height: 84, objectFit: 'cover', borderRadius: 10, flexShrink: 0 }}
              />
              <div style={{ flex: 1, fontSize: 13 }}>
                {photoUploading && <div style={{ color: 'var(--muted)' }}>照片上传中…</div>}
                {!photoUploading && photoUrl && <div className="status-ok">照片已上传</div>}

                {ocrStatus === 'recognizing' && (
                  <div style={{ color: 'var(--muted)', marginTop: 4 }}>
                    识别中 {ocrProgress}%（首次使用需要加载识别模型，稍等一下）
                  </div>
                )}
                {ocrStatus === 'done' && (
                  <div style={{ marginTop: 4 }}>
                    <div className="status-ok">识别完成，已尝试填入产品名称，请核对</div>
                    {recognizedText && (
                      <details style={{ marginTop: 4 }}>
                        <summary style={{ cursor: 'pointer', color: 'var(--muted)' }}>查看识别到的文字</summary>
                        <div style={{ whiteSpace: 'pre-wrap', color: 'var(--muted)', marginTop: 4 }}>
                          {recognizedText}
                        </div>
                      </details>
                    )}
                  </div>
                )}
                {ocrStatus === 'error' && <div className="status-expired" style={{ marginTop: 4 }}>识别失败，可手动填写</div>}

                <button
                  type="button"
                  onClick={handleClearPhoto}
                  style={{
                    border: 'none',
                    background: 'none',
                    color: 'var(--muted)',
                    fontSize: 13,
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    marginTop: 6,
                    padding: 0
                  }}
                >
                  重新拍摄 / 移除照片
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

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
        <button
          type="button"
          className="btn-primary"
          style={{ background: 'white', color: 'var(--pink-500)', border: '1px solid var(--pink-400)' }}
          onClick={handleLookup}
          disabled={!form.name.trim() && !form.brand.trim()}
        >
          {lookupStatus === 'searching' ? '查询中…' : '🔍 联网查询产品信息（品牌/成分）'}
        </button>

        {lookupStatus === 'error' && (
          <div className="status-expired" style={{ fontSize: 13, marginTop: 6 }}>
            查询失败：{lookupError}
          </div>
        )}
        {lookupStatus === 'empty' && (
          <div className="empty-state" style={{ padding: '8px 0' }}>未找到匹配的产品，可继续手动填写</div>
        )}

        {lookupStatus === 'results' && (
          <div style={{ marginTop: 8 }}>
            {lookupResults.map((product, idx) => (
              <button
                key={product.code || idx}
                type="button"
                onClick={() => handleApplyResult(product)}
                className="card"
                style={{
                  display: 'flex',
                  gap: 10,
                  alignItems: 'center',
                  width: '100%',
                  textAlign: 'left',
                  cursor: 'pointer',
                  marginBottom: 8,
                  padding: 10
                }}
              >
                {product.image_small_url ? (
                  <img
                    src={product.image_small_url}
                    alt={product.product_name}
                    style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 8, flexShrink: 0 }}
                  />
                ) : (
                  <div style={{ width: 40, height: 40, borderRadius: 8, background: 'var(--pink-100)', flexShrink: 0 }} />
                )}
                <div style={{ fontSize: 13 }}>
                  <div style={{ fontWeight: 600 }}>{product.product_name}</div>
                  <div style={{ color: 'var(--muted)' }}>{product.brands || '品牌未知'}</div>
                </div>
              </button>
            ))}
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>数据来源：Open Beauty Facts（开源化妆品数据库）</div>
          </div>
        )}

        {appliedResult && (
          <div className="card" style={{ marginTop: 8, padding: 10, fontSize: 13 }}>
            <div className="status-ok">
              已从「{appliedResult.name}」带入品牌
              {appliedResult.matchedTags.length > 0 ? `和 ${appliedResult.matchedTags.length} 个已知成分标签` : ''}
              ，请核对
            </div>
            {appliedResult.ingredientsText && (
              <details style={{ marginTop: 4 }}>
                <summary style={{ cursor: 'pointer', color: 'var(--muted)' }}>查看完整成分表原文</summary>
                <div style={{ whiteSpace: 'pre-wrap', color: 'var(--muted)', marginTop: 4 }}>
                  {appliedResult.ingredientsText}
                </div>
              </details>
            )}
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>数据来源：Open Beauty Facts</div>
          </div>
        )}
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
        {submitting ? '保存中…' : isEditMode ? '保存修改' : '保存产品'}
      </button>
    </form>
  );
}
