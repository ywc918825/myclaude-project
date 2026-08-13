const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const router = express.Router();

const UPLOAD_DIR = path.join(__dirname, '..', 'uploads');
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const EXT_BY_MIME = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp'
};

router.post('/', (req, res) => {
  const { imageBase64 } = req.body || {};
  if (typeof imageBase64 !== 'string' || !imageBase64.startsWith('data:image/')) {
    return res.status(400).json({ error: 'imageBase64 must be a data:image/... base64 string' });
  }

  const match = imageBase64.match(/^data:(image\/[a-zA-Z+]+);base64,(.+)$/);
  if (!match) {
    return res.status(400).json({ error: 'malformed data URL' });
  }

  const [, mime, base64Data] = match;
  const ext = EXT_BY_MIME[mime] || 'jpg';
  const filename = `${Date.now()}-${crypto.randomBytes(6).toString('hex')}.${ext}`;

  fs.writeFileSync(path.join(UPLOAD_DIR, filename), Buffer.from(base64Data, 'base64'));

  res.status(201).json({ url: `/uploads/${filename}` });
});

module.exports = router;
