const express = require('express');
const router = express.Router();
const rules = require('../data/ingredientRules');

function findRule(ingredientA, ingredientB) {
  return rules.find(
    (rule) =>
      (rule.a === ingredientA && rule.b === ingredientB) ||
      (rule.a === ingredientB && rule.b === ingredientA)
  );
}

router.post('/', (req, res) => {
  const { products } = req.body || {};

  if (!Array.isArray(products)) {
    return res.status(400).json({ error: 'products must be an array' });
  }

  const hits = [];

  for (let i = 0; i < products.length; i++) {
    for (let j = i + 1; j < products.length; j++) {
      const productA = products[i];
      const productB = products[j];
      const tagsA = Array.isArray(productA.ingredientTags) ? productA.ingredientTags : [];
      const tagsB = Array.isArray(productB.ingredientTags) ? productB.ingredientTags : [];

      for (const ingredientA of tagsA) {
        for (const ingredientB of tagsB) {
          const rule = findRule(ingredientA, ingredientB);
          if (rule) {
            hits.push({
              productAId: productA.id,
              productAName: productA.name,
              productBId: productB.id,
              productBName: productB.name,
              ingredientA,
              ingredientB,
              reason: rule.reason,
            });
          }
        }
      }
    }
  }

  res.json(hits);
});

module.exports = router;
