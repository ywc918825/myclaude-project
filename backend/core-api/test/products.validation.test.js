const { test } = require('node:test');
const assert = require('node:assert/strict');
const { validateProductInput } = require('../routes/products');

const validBody = {
  name: '保湿面霜',
  brand: 'CeraVe',
  category: '护肤',
  openedDate: '2026-01-01',
  paoMonths: 12,
  ingredientTags: ['神经酰胺'],
  costCNY: 129
};

test('validateProductInput: accepts a well-formed product', () => {
  assert.deepEqual(validateProductInput(validBody), []);
});

test('validateProductInput: rejects missing/blank name', () => {
  const errors = validateProductInput({ ...validBody, name: '  ' });
  assert.ok(errors.length > 0);
});

test('validateProductInput: rejects missing category', () => {
  const errors = validateProductInput({ ...validBody, category: '' });
  assert.ok(errors.length > 0);
});

test('validateProductInput: rejects malformed openedDate', () => {
  const errors = validateProductInput({ ...validBody, openedDate: '2026/01/01' });
  assert.ok(errors.length > 0);
});

test('validateProductInput: rejects non-numeric or non-positive paoMonths', () => {
  assert.ok(validateProductInput({ ...validBody, paoMonths: 'twelve' }).length > 0);
  assert.ok(validateProductInput({ ...validBody, paoMonths: 0 }).length > 0);
  assert.ok(validateProductInput({ ...validBody, paoMonths: -3 }).length > 0);
});

test('validateProductInput: rejects non-array ingredientTags', () => {
  const errors = validateProductInput({ ...validBody, ingredientTags: '维生素C' });
  assert.ok(errors.length > 0);
});

test('validateProductInput: missing body entirely produces errors, not a throw', () => {
  assert.doesNotThrow(() => validateProductInput(undefined));
  assert.ok(validateProductInput(undefined).length > 0);
});
