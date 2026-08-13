const path = require('path');
const Database = require('better-sqlite3');

const db = new Database(path.join(__dirname, 'data.db'));

db.exec(`
  CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT NOT NULL,
    openedDate TEXT NOT NULL,
    paoMonths INTEGER NOT NULL,
    ingredientTags TEXT NOT NULL DEFAULT '[]',
    costCNY REAL DEFAULT 0,
    photoUrl TEXT,
    createdAt TEXT NOT NULL
  );
`);

function monthsAgoISODate(months) {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().slice(0, 10);
}

function seedIfEmpty() {
  const row = db.prepare('SELECT COUNT(*) as c FROM products').get();
  if (row.c > 0) return;

  const seedRows = [
    { name: '烟酰胺精华', brand: 'The Ordinary', category: '护肤', openedDate: monthsAgoISODate(11), paoMonths: 12, ingredientTags: ['烟酰胺'], costCNY: 89 },
    { name: '保湿面霜', brand: 'CeraVe', category: '护肤', openedDate: monthsAgoISODate(2), paoMonths: 18, ingredientTags: ['神经酰胺', '玻尿酸'], costCNY: 129 },
    { name: '视黄醇眼霜', brand: 'RoC', category: '护肤', openedDate: monthsAgoISODate(13), paoMonths: 12, ingredientTags: ['视黄醇(A醇)'], costCNY: 158 },
    { name: '粉底液', brand: 'Fenty Beauty', category: '彩妆', openedDate: monthsAgoISODate(5), paoMonths: 12, ingredientTags: [], costCNY: 320 },
    { name: '滋润口红', brand: 'Chanel', category: '彩妆', openedDate: monthsAgoISODate(20), paoMonths: 24, ingredientTags: ['维生素E'], costCNY: 360 },
    { name: '身体乳', brand: 'NIVEA', category: '身体护理', openedDate: monthsAgoISODate(3), paoMonths: 12, ingredientTags: ['尿素'], costCNY: 59 },
    { name: '维C精华', brand: 'SkinCeuticals', category: '护肤', openedDate: monthsAgoISODate(1), paoMonths: 6, ingredientTags: ['维生素C'], costCNY: 890 },
    { name: '水杨酸精华', brand: 'Paula\'s Choice', category: '护肤', openedDate: monthsAgoISODate(4), paoMonths: 12, ingredientTags: ['水杨酸'], costCNY: 210 }
  ];

  const insert = db.prepare(`
    INSERT INTO products (name, brand, category, openedDate, paoMonths, ingredientTags, costCNY, photoUrl, createdAt)
    VALUES (@name, @brand, @category, @openedDate, @paoMonths, @ingredientTags, @costCNY, @photoUrl, @createdAt)
  `);

  const now = new Date().toISOString();
  const tx = db.transaction((rows) => {
    for (const r of rows) {
      insert.run({
        ...r,
        ingredientTags: JSON.stringify(r.ingredientTags),
        photoUrl: null,
        createdAt: now
      });
    }
  });
  tx(seedRows);
}

seedIfEmpty();

module.exports = db;
