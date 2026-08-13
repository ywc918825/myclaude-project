const express = require('express');
const router = express.Router();
const db = require('../db');
const { addMonths, daysFromToday, statusFromDaysRemaining } = require('../dateUtils');

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

// Required-field validation at the API boundary — this used to be entirely
// unvalidated, so a malformed request (missing openedDate, non-numeric
// paoMonths, etc.) would either 500 or silently write a broken row.
function validateProductInput(body) {
  const errors = [];
  if (!body || typeof body.name !== 'string' || !body.name.trim()) errors.push('name 不能为空');
  if (!body || typeof body.category !== 'string' || !body.category.trim()) errors.push('category 不能为空');
  if (!body || typeof body.openedDate !== 'string' || !DATE_RE.test(body.openedDate)) {
    errors.push('openedDate 必须是 YYYY-MM-DD 格式');
  }
  const paoMonths = Number(body && body.paoMonths);
  if (!Number.isFinite(paoMonths) || paoMonths <= 0) errors.push('paoMonths 必须是正数');
  if (body && body.ingredientTags !== undefined && !Array.isArray(body.ingredientTags)) {
    errors.push('ingredientTags 必须是数组');
  }
  return errors;
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
  const validationErrors = validateProductInput(req.body);
  if (validationErrors.length > 0) {
    return res.status(400).json({ error: validationErrors.join('; ') });
  }

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

  const validationErrors = validateProductInput(req.body);
  if (validationErrors.length > 0) {
    return res.status(400).json({ error: validationErrors.join('; ') });
  }

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

router.validateProductInput = validateProductInput; // exposed for unit tests
module.exports = router;
