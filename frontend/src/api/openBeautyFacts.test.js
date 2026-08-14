import { describe, it, expect, vi, afterEach } from 'vitest';
import { searchOpenBeautyFacts, matchKnownIngredients, getProductByBarcode } from './openBeautyFacts.js';

const VOCAB = ['烟酰胺', '苯氧乙醇', '玻尿酸', '维生素C', '视黄醇(A醇)'];

describe('matchKnownIngredients', () => {
  it('matches English INCI names against the Chinese vocab', () => {
    const matched = matchKnownIngredients(
      'Sodium Hyaluronate, Niacinamide, Phenoxyethanol, Aqua',
      '',
      VOCAB
    );
    expect(matched.sort()).toEqual(['烟酰胺', '玻尿酸', '苯氧乙醇'].sort());
  });

  it('matches directly on Chinese ingredients_text_zh when present', () => {
    const matched = matchKnownIngredients('', '水、烟酰胺、甘油', VOCAB);
    expect(matched).toEqual(['烟酰胺']);
  });

  it('returns empty array when nothing matches', () => {
    expect(matchKnownIngredients('Aqua, Glycerin', '', VOCAB)).toEqual([]);
  });

  it('handles missing/undefined ingredient text without throwing', () => {
    expect(() => matchKnownIngredients(undefined, undefined, VOCAB)).not.toThrow();
    expect(matchKnownIngredients(undefined, undefined, VOCAB)).toEqual([]);
  });
});

describe('searchOpenBeautyFacts', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns an empty array for a blank query without calling fetch', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    const results = await searchOpenBeautyFacts('   ');
    expect(results).toEqual([]);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('filters out results with no product_name', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          products: [{ product_name: 'Snail Cream', brands: 'COSRX' }, { brands: 'NoName' }]
        })
      })
    );
    const results = await searchOpenBeautyFacts('snail');
    expect(results).toHaveLength(1);
    expect(results[0].product_name).toBe('Snail Cream');
  });

  it('throws a readable error on a non-ok HTTP response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    await expect(searchOpenBeautyFacts('snail')).rejects.toThrow('503');
  });
});

describe('getProductByBarcode', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns the product when Open Beauty Facts reports status 1', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 1, product: { product_name: 'Snail Cream', brands: 'COSRX' } })
      })
    );
    const product = await getProductByBarcode('6111234567890');
    expect(product).toEqual({ product_name: 'Snail Cream', brands: 'COSRX' });
  });

  it('returns null when the barcode has no match (status 0 in a 200 body)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 0 }) }));
    expect(await getProductByBarcode('0000000000000')).toBeNull();
  });

  it('returns null (not an error) when the barcode has no match reported as a plain HTTP 404', async () => {
    // Field-observed: Open Beauty Facts' v2 product endpoint reports an
    // unrecognized barcode as a 404, not a 200 with status:0 — this used to
    // surface as a scary "查询失败：HTTP 404" instead of the not-found message.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));
    expect(await getProductByBarcode('6900000000000')).toBeNull();
  });

  it('throws a readable error on a genuine non-404 non-ok HTTP response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }));
    await expect(getProductByBarcode('123')).rejects.toThrow('500');
  });

  it('URL-encodes the barcode into the request path', async () => {
    const fetchSpy = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 0 }) });
    vi.stubGlobal('fetch', fetchSpy);
    await getProductByBarcode('123 456');
    expect(fetchSpy.mock.calls[0][0]).toContain('123%20456');
  });
});
