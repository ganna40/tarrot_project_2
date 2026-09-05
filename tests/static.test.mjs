import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');

test('static page exposes the API validator controls', async () => {
  const html = await read('docs/index.html');
  for (const id of [
    'reading-form', 'question', 'card-1', 'card-2', 'card-3',
    'api-dialog', 'api-base-url', 'test-connection',
    'request-json', 'response-json', 'chat-log',
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`));
  }
  assert.match(html, /type=["']module["']/);
});

test('page has no third-party runtime dependencies', async () => {
  const html = await read('docs/index.html');
  assert.doesNotMatch(html, /<(script|link)[^>]+(?:src|href)=[\"']https?:\/\//i);
  assert.match(html, /\.\/styles\.css/);
  assert.match(html, /\.\/assets\/app\.js/);
});

test('API token is never persisted to localStorage', async () => {
  const app = await read('docs/assets/app.js');
  assert.doesNotMatch(app, /localStorage\.setItem\([^\n]*(token|apiKey|api_key)/i);
  assert.match(app, /delete\s+serializable\.token/);
});
