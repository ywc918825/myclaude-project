const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' })); // photo uploads arrive as base64 JSON

require('./db'); // ensures DB file + seed data exist before routes run

app.get('/health', (req, res) => res.json({ ok: true, service: 'core-api' }));

app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

app.use('/api/categories', require('./routes/categories'));
app.use('/api/products', require('./routes/products'));
app.use('/api/upload', require('./routes/upload'));

const PORT = process.env.PORT || 4001;
app.listen(PORT, () => {
  console.log(`core-api listening on http://localhost:${PORT}`);
});
