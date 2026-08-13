// Copies tesseract.js's worker/core/language files from node_modules into
// public/tesseract-assets so OCR runs fully offline (no CDN dependency).
// Runs automatically via the "postinstall" npm script.
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const destDir = path.join(root, 'public', 'tesseract-assets');
fs.mkdirSync(destDir, { recursive: true });

function copy(src, destName) {
  const dest = path.join(destDir, destName || path.basename(src));
  fs.copyFileSync(src, dest);
  console.log(`copied ${path.relative(root, src)} -> ${path.relative(root, dest)}`);
}

copy(path.join(root, 'node_modules/tesseract.js/dist/worker.min.js'));

for (const core of ['tesseract-core.wasm.js', 'tesseract-core-simd.wasm.js', 'tesseract-core-lstm.wasm.js', 'tesseract-core-simd-lstm.wasm.js']) {
  copy(path.join(root, 'node_modules/tesseract.js-core', core));
}

copy(path.join(root, 'node_modules/@tesseract.js-data/eng/4.0.0/eng.traineddata.gz'));
copy(path.join(root, 'node_modules/@tesseract.js-data/chi_sim/4.0.0/chi_sim.traineddata.gz'));

console.log('tesseract assets ready in public/tesseract-assets/');
