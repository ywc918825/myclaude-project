// Open Beauty Facts (world.openbeautyfacts.org) — free, open, crowdsourced
// cosmetics database. No API key required. Data is ODbL-licensed; the UI
// that renders results should credit the source.
const SEARCH_URL = 'https://world.openbeautyfacts.org/api/v2/search';
const PRODUCT_URL = 'https://world.openbeautyfacts.org/api/v2/product';

const FIELDS = ['product_name', 'brands', 'ingredients_text', 'ingredients_text_zh', 'image_small_url', 'code'].join(',');

export async function searchOpenBeautyFacts(query) {
  const trimmed = query.trim();
  if (!trimmed) return [];

  const url = `${SEARCH_URL}?search_terms=${encodeURIComponent(trimmed)}&fields=${FIELDS}&page_size=5`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`查询失败：HTTP ${res.status}`);
  }
  const data = await res.json();
  return (data.products || []).filter((p) => p.product_name);
}

// Barcode lookup is an exact match against Open Beauty Facts' own product
// record (as opposed to searchOpenBeautyFacts' fuzzy text search over
// multiple candidates), so it's much more trustworthy to auto-apply.
// Returns the product object, or null if this barcode isn't in their database.
export async function getProductByBarcode(barcode) {
  const url = `${PRODUCT_URL}/${encodeURIComponent(barcode)}.json?fields=${FIELDS}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`查询失败：HTTP ${res.status}`);
  }
  const data = await res.json();
  if (data.status !== 1 || !data.product) return null;
  return data.product;
}

// Rough Chinese-vocab -> English INCI name mapping, since most Open Beauty
// Facts entries only have ingredients_text in English/French INCI naming.
// This is a best-effort match, not an authoritative ingredient parse.
const INCI_MATCH = {
  '维生素C': ['ascorbic acid', 'ascorbyl'],
  '烟酰胺': ['niacinamide'],
  '视黄醇(A醇)': ['retinol'],
  '水杨酸': ['salicylic acid'],
  '果酸(AHA)': ['glycolic acid', 'lactic acid', 'alpha hydroxy'],
  '苯氧乙醇': ['phenoxyethanol'],
  '尿素': ['urea'],
  '神经酰胺': ['ceramide'],
  '玻尿酸': ['hyaluronic acid', 'sodium hyaluronate'],
  '积雪草': ['centella asiatica', 'centella'],
  '熊果苷': ['arbutin'],
  '传明酸': ['tranexamic acid'],
  '二裂酵母': ['saccharomyces ferment', 'bifida ferment lysate', 'saccharomyces'],
  '维生素E': ['tocopherol'],
  '甘草酸二钾': ['glycyrrhizate', 'glycyrrhiza']
};

export function matchKnownIngredients(ingredientsText, ingredientsTextZh, vocab) {
  const haystackEn = (ingredientsText || '').toLowerCase();
  const zh = ingredientsTextZh || '';
  return vocab.filter((tag) => {
    const zhCore = tag.replace(/[()（）].*$/, '');
    if (zh.includes(zhCore)) return true;
    const needles = INCI_MATCH[tag] || [];
    return needles.some((needle) => haystackEn.includes(needle));
  });
}
