const { test } = require('node:test');
const assert = require('node:assert/strict');
const { buildReport } = require('../reportLogic');

test('buildReport: empty input', () => {
  const report = buildReport([]);
  assert.equal(report.totalItems, 0);
  assert.equal(report.totalValueCNY, 0);
  assert.equal(report.wastedValueCNY, 0);
  assert.deepEqual(report.categoryBreakdown, {});
  assert.deepEqual(report.monthlyOpened, []);
});

test('buildReport: sums totalValueCNY and isolates wastedValueCNY to expired items', () => {
  const products = [
    { category: '护肤', costCNY: 100, status: 'ok', openedDate: '2026-01-10' },
    { category: '护肤', costCNY: 50, status: 'expired', openedDate: '2026-01-15' },
    { category: '彩妆', costCNY: 200, status: 'warning', openedDate: '2026-02-01' }
  ];
  const report = buildReport(products);
  assert.equal(report.totalItems, 3);
  assert.equal(report.totalValueCNY, 350);
  assert.equal(report.wastedValueCNY, 50);
  assert.deepEqual(report.categoryBreakdown, { 护肤: 2, 彩妆: 1 });
});

test('buildReport: groups monthlyOpened by YYYY-MM, sorted ascending, with per-month totals', () => {
  const products = [
    { category: 'x', costCNY: 10, status: 'ok', openedDate: '2026-03-05' },
    { category: 'x', costCNY: 20, status: 'ok', openedDate: '2026-01-20' },
    { category: 'x', costCNY: 5, status: 'ok', openedDate: '2026-01-01' }
  ];
  const report = buildReport(products);
  assert.deepEqual(report.monthlyOpened, [
    { month: '2026-01', count: 2, costCNY: 25 },
    { month: '2026-03', count: 1, costCNY: 10 }
  ]);
});

test('buildReport: treats non-numeric costCNY as 0 instead of NaN-poisoning totals', () => {
  const products = [{ category: 'x', costCNY: 'not-a-number', status: 'ok', openedDate: '2026-01-01' }];
  const report = buildReport(products);
  assert.equal(report.totalValueCNY, 0);
  assert.equal(Number.isNaN(report.totalValueCNY), false);
});

test('buildReport: missing category falls back to "未分类" instead of dropping the item', () => {
  const products = [{ costCNY: 10, status: 'ok', openedDate: '2026-01-01' }];
  const report = buildReport(products);
  assert.deepEqual(report.categoryBreakdown, { 未分类: 1 });
});

test('buildReport: skips monthlyOpened bucketing for malformed openedDate without throwing', () => {
  const products = [{ category: 'x', costCNY: 10, status: 'ok', openedDate: 'bad' }];
  assert.doesNotThrow(() => buildReport(products));
  assert.deepEqual(buildReport(products).monthlyOpened, []);
});
