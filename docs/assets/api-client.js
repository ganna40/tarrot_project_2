export class ApiRequestError extends Error {
  constructor(message, { code = 'API_ERROR', status = null, details = null, cause = null } = {}) {
    super(message, cause ? { cause } : undefined);
    this.name = 'ApiRequestError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export function buildApiUrl(baseUrl, path = '') {
  const normalizedBase = String(baseUrl ?? '').trim();
  if (!normalizedBase) {
    throw new ApiRequestError('API 기본 URL을 입력해 주세요.', { code: 'BASE_URL_REQUIRED' });
  }

  let parsed;
  try {
    parsed = new URL(normalizedBase);
  } catch (cause) {
    throw new ApiRequestError('API URL 형식이 올바르지 않습니다.', { code: 'INVALID_URL', cause });
  }
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new ApiRequestError('API URL은 http 또는 https만 사용할 수 있습니다.', { code: 'INVALID_URL' });
  }

  const cleanBase = normalizedBase.replace(/\/+$/, '');
  const cleanPath = String(path ?? '').trim().replace(/^\/+/, '');
  return cleanPath ? `${cleanBase}/${cleanPath}` : cleanBase;
}

export function buildRequestHeaders(authMode = 'NONE', token = '') {
  const headers = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  const cleanToken = String(token ?? '').trim();
  if (authMode === 'BEARER' && cleanToken) headers.Authorization = `Bearer ${cleanToken}`;
  if (authMode === 'X_API_KEY' && cleanToken) headers['X-API-Key'] = cleanToken;
  return headers;
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') ?? '';
  const text = await response.text();
  if (!text) return null;
  if (contentType.includes('application/json')) {
    try {
      return JSON.parse(text);
    } catch {
      return { raw: text };
    }
  }
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

async function executeRequest({
  url,
  method,
  authMode,
  token,
  payload,
  fetchImpl = fetch,
  timeoutMs = 30000,
}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(url, {
      method,
      mode: 'cors',
      credentials: 'omit',
      cache: 'no-store',
      headers: buildRequestHeaders(authMode, token),
      ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
      signal: controller.signal,
    });
    const data = await parseResponse(response);
    if (!response.ok) {
      const detail = data?.detail ?? data?.message ?? data?.error ?? `HTTP ${response.status}`;
      throw new ApiRequestError(`API 요청이 실패했습니다: ${detail}`, {
        code: 'HTTP_ERROR',
        status: response.status,
        details: data,
      });
    }
    return { status: response.status, data };
  } catch (error) {
    if (error instanceof ApiRequestError) throw error;
    if (error?.name === 'AbortError') {
      throw new ApiRequestError('API 응답 시간이 초과되었습니다.', { code: 'TIMEOUT', cause: error });
    }
    throw new ApiRequestError('API에 연결하지 못했습니다. URL, HTTPS, CORS 설정을 확인해 주세요.', {
      code: 'NETWORK_ERROR',
      cause: error,
    });
  } finally {
    clearTimeout(timer);
  }
}

export async function requestConsultation({
  baseUrl,
  endpoint = '/api/consultation',
  payload,
  authMode = 'NONE',
  token = '',
  fetchImpl = fetch,
  timeoutMs = 30000,
}) {
  return executeRequest({
    url: buildApiUrl(baseUrl, endpoint),
    method: 'POST',
    authMode,
    token,
    payload,
    fetchImpl,
    timeoutMs,
  });
}

export async function checkHealth({
  baseUrl,
  healthPath = '/health',
  authMode = 'NONE',
  token = '',
  fetchImpl = fetch,
  timeoutMs = 10000,
}) {
  return executeRequest({
    url: buildApiUrl(baseUrl, healthPath),
    method: 'GET',
    authMode,
    token,
    payload: undefined,
    fetchImpl,
    timeoutMs,
  });
}
