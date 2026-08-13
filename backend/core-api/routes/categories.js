const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json(['护肤', '彩妆', '身体护理']);
});

module.exports = router;
