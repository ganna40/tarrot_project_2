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
    'llm-model', 'llm-reasoning-effort', 'interpretation-style',
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

test('frontend exposes a Local Codex preset that targets the local v1 reading API', async () => {
  const [html, app] = await Promise.all([
    read('docs/index.html'),
    read('docs/assets/app.js'),
  ]);

  assert.match(html, /option\s+value=["']LOCAL_CODEX["'][^>]*>\s*로컬 Codex/);
  assert.match(app, /LOCAL_CODEX_SETTINGS/);
  assert.match(app, /http:\/\/127\.0\.0\.1:8000/);
  assert.match(app, /\/api\/v1\/readings/);
  assert.match(app, /URLSearchParams/);
  assert.match(app, /local-codex/i);
});

test('Local Codex web mode defaults to GPT-5.6 Sol, xhigh, rich, and detailed', async () => {
  const [html, app] = await Promise.all([
    read('docs/index.html'),
    read('docs/assets/app.js'),
  ]);

  assert.match(html, /id=["']llm-model["']/);
  assert.match(html, /gpt-5\.6-sol/);
  assert.match(html, /id=["']llm-reasoning-effort["']/);
  assert.match(html, /value=["']XHIGH["']/);
  assert.match(html, /id=["']interpretation-style["']/);
  assert.match(html, /value=["']RICH["']/);
  assert.match(html, /Temperature.*Codex CLI.*기본/i);
  assert.match(app, /llmModel/);
  assert.match(app, /llmReasoningEffort/);
  assert.match(app, /interpretationStyle/);
  assert.match(app, /responseLength\.value\s*=\s*['"]DETAILED['"]/);
});

test('one-command local web launcher starts backend, static frontend, and opens Local Codex mode', async () => {
  const script = await read('scripts/run_codex_web.ps1');

  assert.match(script, /LLM_PROVIDER/);
  assert.match(script, /codex_subscription/);
  assert.match(script, /uvicorn/);
  assert.match(script, /http\.server/);
  assert.match(script, /127\.0\.0\.1:8080/);
  assert.match(script, /mode=local-codex/i);
});
