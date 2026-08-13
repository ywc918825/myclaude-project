const express = require('express');
const router = express.Router();

router.post('/', (req, res) => {
  const { products } = req.body || {};

  if (!Array.isArray(products)) {
    return res.status(400).json({ error: 'products must be an array' });
  }

  const totalItems = products.length;
  let totalValueCNY = 0;
  let wastedValueCNY = 0;
  const categoryBreakdown = {};
  const monthlyMap = {};

  for (const product of products) {
    const cost = Number(product.costCNY) || 0;
    totalValueCNY += cost;

    if (product.status === 'expired') {
      wastedValueCNY += cost;
    }

    const category = product.category || '未分类';
    categoryBreakdown[category] = (categoryBreakdown[category] || 0) + 1;

    if (typeof product.openedDate === 'string' && product.openedDate.length >= 7) {
      const month = product.openedDate.slice(0, 7); // "YYYY-MM"
      if (!monthlyMap[month]) {
        monthlyMap[month] = { month, count: 0, costCNY: 0 };
      }
      monthlyMap[month].count += 1;
      monthlyMap[month].costCNY += cost;
    }
  }

  const monthlyOpened = Object.values(monthlyMap).sort((a, b) =>
    a.month.localeCompare(b.month)
  );

  res.json({
    totalItems,
    totalValueCNY,
    wastedValueCNY,
    categoryBreakdown,
    monthlyOpened,
  });
});

module.exports = router;
