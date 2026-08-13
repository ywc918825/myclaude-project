const express = require('express');
const router = express.Router();
const { buildReport } = require('../reportLogic');

router.post('/', (req, res) => {
  const { products } = req.body || {};

  if (!Array.isArray(products)) {
    return res.status(400).json({ error: 'products must be an array' });
  }

  res.json(buildReport(products));
});

module.exports = router;
