const express = require('express');
const router = express.Router();
const rules = require('../data/ingredientRules');
const { buildConflictHits } = require('../conflictLogic');

router.post('/', (req, res) => {
  const { products } = req.body || {};

  if (!Array.isArray(products)) {
    return res.status(400).json({ error: 'products must be an array' });
  }

  res.json(buildConflictHits(products, rules));
});

module.exports = router;
