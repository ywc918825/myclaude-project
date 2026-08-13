const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

require('./db'); // ensures DB file + seed data exist before routes run

app.get('/health', (req, res) => res.json({ ok: true, service: 'core-api' }));

app.use('/api/categories', require('./routes/categories'));
app.use('/api/products', require('./routes/products'));

const PORT = process.env.PORT || 4001;
app.listen(PORT, () => {
  console.log(`core-api listening on http://localhost:${PORT}`);
});
