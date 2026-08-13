const express = require('express');
const router = express.Router();
const db = require('../db');

// ---- date helpers (no extra deps) ----

// Add `months` calendar months to a "YYYY-MM-DD" date string, return "YYYY-MM-DD".
function addMonths(dateStr, months) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  date.setUTCMonth(date.getUTCMonth() + months);
  return date.toISOString().slice(0, 10);
}

// Integer day difference from today (UTC midnight) to target "YYYY-MM-DD" date.
function daysFromToday(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const target = Date.UTC(y, m - 1, d);

  const now = new Date();
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());

  const MS_PER_DAY = 24 * 60 * 60 * 1000;
  return Math.round((target - today) / MS_PER_DAY);
}

function statusFromDaysRemaining(daysRemaining) {
  if (daysRemaining < 0) return 'expired';
  if (daysRemaining <= 14) return 'warning';
  return 'ok';
}

// Convert a raw DB row (ingredientTags stored as JSON string) into the full
// API-facing Product shape with computed fields.
function toApiProduct(row) {
  const expiryDate = addMonths(row.openedDate, row.paoMonths);
  const daysRemaining = daysFromToday(expiryDate);
  const status = statusFromDaysRemaining(daysRemaining);

  return {
    ...row,
    ingredientTags: JSON.parse(row.ingredientTags || '[]'),
    expiryDate,
    daysRemaining,
    status
  };
}

// ---- routes ----

router.get('/', (req, res) => {
  const rows = db.prepare('SELECT * FROM products ORDER BY id').all();
  res.json(rows.map(toApiProduct));
});

router.get('/:id', (req, res) => {
  const row = db.prepare('SELECT * FROM products WHERE id = ?').get(req.params.id);
  if (!row) return res.status(404).json({ error: 'not found' });
  res.json(toApiProduct(row));
});

router.post('/', (req, res) => {
  const { name, brand, category, openedDate, paoMonths, ingredientTags, costCNY, photoUrl } = req.body;
  const createdAt = new Date().toISOString();

  const insert = db.prepare(`
    INSERT INTO products (name, brand, category, openedDate, paoMonths, ingredientTags, costCNY, photoUrl, createdAt)
    VALUES (@name, @brand, @category, @openedDate, @paoMonths, @ingredientTags, @costCNY, @photoUrl, @createdAt)
  `);

  const info = insert.run({
    name,
    brand: brand ?? null,
    category,
    openedDate,
    paoMonths,
    ingredientTags: JSON.stringify(ingredientTags ?? []),
    costCNY: costCNY ?? 0,
    photoUrl: photoUrl ?? null,
    createdAt
  });

  const row = db.prepare('SELECT * FROM products WHERE id = ?').get(info.lastInsertRowid);
  res.status(201).json(toApiProduct(row));
});

router.put('/:id', (req, res) => {
  const existing = db.prepare('SELECT * FROM products WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'not found' });

  const { name, brand, category, openedDate, paoMonths, ingredientTags, costCNY, photoUrl } = req.body;

  const update = db.prepare(`
    UPDATE products
    SET name = @name,
        brand = @brand,
        category = @category,
        openedDate = @openedDate,
        paoMonths = @paoMonths,
        ingredientTags = @ingredientTags,
        costCNY = @costCNY,
        photoUrl = @photoUrl
    WHERE id = @id
  `);

  update.run({
    id: req.params.id,
    name,
    brand: brand ?? null,
    category,
    openedDate,
    paoMonths,
    ingredientTags: JSON.stringify(ingredientTags ?? []),
    costCNY: costCNY ?? 0,
    photoUrl: photoUrl ?? null
  });

  const row = db.prepare('SELECT * FROM products WHERE id = ?').get(req.params.id);
  res.json(toApiProduct(row));
});

router.delete('/:id', (req, res) => {
  const existing = db.prepare('SELECT * FROM products WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'not found' });

  db.prepare('DELETE FROM products WHERE id = ?').run(req.params.id);
  res.status(204).end();
});

module.exports = router;
