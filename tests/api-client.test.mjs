import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ApiRequestError,
  buildApiUrl,
  buildRequestHeaders,
  checkHealth,
  requestConsultation,
} from '../docs/assets/api-client.js';

test('joins a base URL and endpoint without duplicate slashes', () => {
  assert.equal(buildApiUrl('https://api.example.com/', '/api/consultation'), 'https://api.example.com/api/consultation');
});

test('rejects a non-http API URL', () => {
  assert.throws(() => buildApiUrl('javascript:alert(1)', '/api'), ApiRequestError);
});

test('builds bearer and x-api-key headers without storing policy', () => {
  assert.deepEqual(buildRequestHeaders('BEARER', 'secret'), {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Authorization: 'Bearer secret',
  });
  assert.equal(buildRequestHeaders('X_API_KEY', 'secret')['X-API-Key'], 'secret');
});

test('posts a consultation and parses JSON', async () => {
  const calls = [];
  const fakeFetch = async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ verdict: 'POSITIVE' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  const result = await requestConsultation({
    baseUrl: 'https://api.example.com',
    endpoint: '/api/consultation',
    payload: { question: 'test' },
    authMode: 'NONE',
    token: '',
    fetchImpl: fakeFetch,
    timeoutMs: 100,
  });

  assert.equal(result.data.verdict, 'POSITIVE');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].options.credentials, 'omit');
});

test('maps HTTP errors to ApiRequestError with response details', async () => {
  const fakeFetch = async () => new Response(JSON.stringify({ detail: 'bad card' }), {
    status: 422,
    headers: { 'Content-Type': 'application/json' },
  });

  await assert.rejects(
    requestConsultation({
      baseUrl: 'https://api.example.com',
      endpoint: '/api/consultation',
      payload: {},
      authMode: 'NONE',
      token: '',
      fetchImpl: fakeFetch,
      timeoutMs: 100,
    }),
    (error) => error instanceof ApiRequestError && error.status === 422 && error.details.detail === 'bad card',
  );
});

test('checks a custom health endpoint', async () => {
  const fakeFetch = async (url, options) => {
    assert.equal(url, 'https://api.example.com/health');
    assert.equal(options.method, 'GET');
    return new Response(JSON.stringify({ status: 'healthy' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  const result = await checkHealth({
    baseUrl: 'https://api.example.com/',
    healthPath: '/health',
    authMode: 'NONE',
    token: '',
    fetchImpl: fakeFetch,
    timeoutMs: 100,
  });
  assert.equal(result.data.status, 'healthy');
});
