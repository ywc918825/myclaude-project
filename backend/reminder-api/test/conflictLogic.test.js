const { test } = require('node:test');
const assert = require('node:assert/strict');
const { findRule, buildConflictHits } = require('../conflictLogic');

const rules = [
  { a: '维生素C', b: '烟酰胺', reason: 'reason-vc-niacin' },
  { a: '视黄醇(A醇)', b: '水杨酸', reason: 'reason-retinol-sa' }
];

test('findRule: matches regardless of argument order', () => {
  assert.ok(findRule(rules, '维生素C', '烟酰胺'));
  assert.ok(findRule(rules, '烟酰胺', '维生素C'));
  assert.equal(findRule(rules, '维生素C', '水杨酸'), undefined);
});

test('buildConflictHits: flags a conflicting pair across two products', () => {
  const products = [
    { id: 1, name: 'A精华', ingredientTags: ['维生素C'] },
    { id: 2, name: 'B精华', ingredientTags: ['烟酰胺'] }
  ];
  const hits = buildConflictHits(products, rules);
  assert.equal(hits.length, 1);
  assert.equal(hits[0].productAId, 1);
  assert.equal(hits[0].productBId, 2);
  assert.equal(hits[0].reason, 'reason-vc-niacin');
});

test('buildConflictHits: no hits when no products share a conflicting pair', () => {
  const products = [
    { id: 1, name: 'A', ingredientTags: ['玻尿酸'] },
    { id: 2, name: 'B', ingredientTags: ['神经酰胺'] }
  ];
  assert.deepEqual(buildConflictHits(products, rules), []);
});

test('buildConflictHits: does not flag a product against itself', () => {
  const products = [{ id: 1, name: 'A', ingredientTags: ['维生素C', '烟酰胺'] }];
  assert.deepEqual(buildConflictHits(products, rules), []);
});

test('buildConflictHits: tolerates missing/non-array ingredientTags', () => {
  const products = [
    { id: 1, name: 'A' },
    { id: 2, name: 'B', ingredientTags: ['维生素C'] }
  ];
  assert.doesNotThrow(() => buildConflictHits(products, rules));
  assert.deepEqual(buildConflictHits(products, rules), []);
});

test('buildConflictHits: only compares across different products, not within one', () => {
  const products = [
    { id: 1, name: 'A', ingredientTags: ['维生素C'] },
    { id: 2, name: 'B', ingredientTags: ['烟酰胺'] },
    // C's own two tags conflict with each other per the rule table, but that's
    // not what this feature checks — it only flags pairs across two products.
    { id: 3, name: 'C', ingredientTags: ['视黄醇(A醇)', '水杨酸'] }
  ];
  const hits = buildConflictHits(products, rules);
  assert.equal(hits.length, 1);
  assert.equal(hits[0].productAId, 1);
  assert.equal(hits[0].productBId, 2);
});
