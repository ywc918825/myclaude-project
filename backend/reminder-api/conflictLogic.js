function findRule(rules, ingredientA, ingredientB) {
  return rules.find(
    (rule) =>
      (rule.a === ingredientA && rule.b === ingredientB) ||
      (rule.a === ingredientB && rule.b === ingredientA)
  );
}

// Pairwise-compares every product's ingredientTags against the rule table
// and returns one hit per conflicting ingredient pair found.
function buildConflictHits(products, rules) {
  const hits = [];

  for (let i = 0; i < products.length; i++) {
    for (let j = i + 1; j < products.length; j++) {
      const productA = products[i];
      const productB = products[j];
      const tagsA = Array.isArray(productA.ingredientTags) ? productA.ingredientTags : [];
      const tagsB = Array.isArray(productB.ingredientTags) ? productB.ingredientTags : [];

      for (const ingredientA of tagsA) {
        for (const ingredientB of tagsB) {
          const rule = findRule(rules, ingredientA, ingredientB);
          if (rule) {
            hits.push({
              productAId: productA.id,
              productAName: productA.name,
              productBId: productB.id,
              productBName: productB.name,
              ingredientA,
              ingredientB,
              reason: rule.reason
            });
          }
        }
      }
    }
  }

  return hits;
}

module.exports = { findRule, buildConflictHits };
