import { describe, it, expect, vi, afterEach } from 'vitest';
import { searchOpenBeautyFacts, matchKnownIngredients } from './openBeautyFacts.js';

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
