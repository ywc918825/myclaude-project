const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => res.json({ ok: true, service: 'reminder-api' }));

app.use('/api/ingredient-rules', (req, res) => {
  res.json(require('./data/ingredientRules'));
});
app.use('/api/conflict-check', require('./routes/conflict'));
app.use('/api/report', require('./routes/report'));

const PORT = process.env.PORT || 4002;
app.listen(PORT, () => {
  console.log(`reminder-api listening on http://localhost:${PORT}`);
});
