import { access, readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const required = [
  'docs/index.html',
  'docs/styles.css',
  'docs/.nojekyll',
  'docs/assets/app.js',
  'docs/assets/cards.js',
  'docs/assets/payload.js',
  'docs/assets/api-client.js',
  'docs/assets/response.js',
  'docs/assets/demo.js',
];

for (const relative of required) await access(resolve(root, relative));

const html = await readFile(resolve(root, 'docs/index.html'), 'utf8');
if (!html.includes('type="module"')) throw new Error('index.html must load app.js as an ES module');
if (/<(script|link)[^>]+(?:src|href)=["']https?:\/\//i.test(html)) {
  throw new Error('Third-party runtime assets are not allowed');
}

const app = await readFile(resolve(root, 'docs/assets/app.js'), 'utf8');
if (/localStorage\.setItem\([^\n]*(token|apiKey|api_key)/i.test(app)) {
  throw new Error('API token must not be persisted');
}

console.log(`Static validation passed: ${required.length} required files, no remote runtime assets, no persisted API token.`);
