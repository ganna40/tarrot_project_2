import { TAROT_CARDS, formatCardLabel, getCard, groupLabel } from './cards.js';
import { buildConsultationPayload, ReadingValidationError } from './payload.js';
import { ApiRequestError, checkHealth, requestConsultation } from './api-client.js';
import { normalizeTarotResponse, verdictLabel } from './response.js';
import { runDemoConsultation } from './demo.js';

const SETTINGS_KEY = 'tarot-engine-validator-settings-v1';
const DEFAULT_SETTINGS = Object.freeze({
  mode: 'DEMO',
  baseUrl: 'http://localhost:8000',
  endpoint: '/api/consultation',
  healthPath: '/health',
  authMode: 'NONE',
  timeoutMs: 30000,
});
const LOCAL_CODEX_SETTINGS = Object.freeze({
  mode: 'LOCAL_CODEX',
  baseUrl: 'http://127.0.0.1:8000',
  endpoint: '/api/v1/readings',
  healthPath: '/health',
  authMode: 'NONE',
  timeoutMs: 210000,
});

const STYLE_LABELS = Object.freeze({
  PRECISE: '정확하게',
  BALANCED: '균형',
  RICH: '풍부하게',
});

const state = {
  settings: loadSettings(),
  token: '',
  busy: false,
};

const $ = (id) => document.getElementById(id);
const elements = {
  form: $('reading-form'),
  question: $('question'),
  additionalContext: $('additional-context'),
  readingContext: $('reading-context'),
  responseLength: $('response-length'),
  llmModel: $('llm-model'),
  llmReasoningEffort: $('llm-reasoning-effort'),
  interpretationStyle: $('interpretation-style'),
  useLlm: $('use-llm'),
  includeTrace: $('include-trace'),
  submit: $('submit-reading'),
  randomize: $('randomize-cards'),
  chatLog: $('chat-log'),
  clearChat: $('clear-chat'),
  requestJson: $('request-json'),
  responseJson: $('response-json'),
  traceJson: $('trace-json'),
  modeHint: $('mode-hint'),
  connectionStatus: $('connection-status'),
  dialog: $('api-dialog'),
  openSettings: $('open-api-settings'),
  closeSettings: $('close-api-settings'),
  settingsForm: $('api-settings-form'),
  connectionMode: $('connection-mode'),
  baseUrl: $('api-base-url'),
  endpoint: $('api-endpoint'),
  healthPath: $('health-path'),
  authMode: $('auth-mode'),
  token: $('api-token'),
  testConnection: $('test-connection'),
  testResult: $('connection-test-result'),
};

function requestedLocalCodexMode() {
  const params = new URLSearchParams(globalThis.location?.search ?? '');
  return (params.get('mode') ?? '').toLowerCase() === 'local-codex';
}

function normalizeSavedSettings(saved) {
  if (saved.mode === 'LOCAL_CODEX') return { ...LOCAL_CODEX_SETTINGS };
  if (saved.mode === 'REMOTE') return { ...DEFAULT_SETTINGS, ...saved, mode: 'REMOTE' };
  return { ...DEFAULT_SETTINGS, ...saved, mode: 'DEMO' };
}

function loadSettings() {
  if (requestedLocalCodexMode()) return { ...LOCAL_CODEX_SETTINGS };
  try {
    const saved = JSON.parse(localStorage.getItem(SETTINGS_KEY) ?? '{}');
    return normalizeSavedSettings(saved);
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

function persistSettings(settings) {
  const serializable = { ...settings };
  delete serializable.token;
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(serializable));
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function createOption(card) {
  const option = document.createElement('option');
  option.value = card.code;
  option.textContent = formatCardLabel(card);
  return option;
}

function populateCardSelect(select) {
  const groups = new Map();
  for (const card of TAROT_CARDS) {
    const label = groupLabel(card);
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(card);
  }
  for (const [label, cards] of groups) {
    const group = document.createElement('optgroup');
    group.label = label;
    cards.forEach((card) => group.append(createOption(card)));
    select.append(group);
  }
}

function selectedCards() {
  return [1, 2, 3].map((number) => ({
    code: $(`card-${number}`).value,
    orientation: $(`orientation-${number}`).value,
  }));
}

function cardSummary(cards) {
  return cards.map(({ code, orientation }) => {
    const card = getCard(code);
    return `${card.nameKo} ${orientation === 'REVERSED' ? '역방향' : '정방향'}`;
  }).join(' → ');
}

function appendMessage({ role, text = '', meta = '', tags = [], flow = '', advice = '', pending = false }) {
  const article = document.createElement('article');
  article.className = `message message-${role}`;
  if (pending) article.dataset.pending = 'true';

  const label = document.createElement('p');
  label.className = 'message-meta';
  label.textContent = meta || ({ user: 'YOU', assistant: 'TAROT ENGINE', system: 'SYSTEM', error: 'ERROR' }[role] ?? role);
  article.append(label);

  if (tags.length) {
    const tagBox = document.createElement('div');
    tagBox.className = 'message-tags';
    tags.forEach(({ label: tagLabel, variant = '' }) => {
      const tag = document.createElement('span');
      tag.className = `message-tag ${variant}`.trim();
      tag.textContent = tagLabel;
      tagBox.append(tag);
    });
    article.append(tagBox);
  }

  if (flow) {
    const flowLine = document.createElement('p');
    flowLine.className = 'message-flow';
    flowLine.textContent = `흐름 · ${flow}`;
    article.append(flowLine);
  }

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  if (pending) {
    const typing = document.createElement('span');
    typing.className = 'typing';
    typing.setAttribute('aria-label', '응답 대기 중');
    typing.append(document.createElement('i'), document.createElement('i'), document.createElement('i'));
    bubble.append(typing);
  } else {
    const body = document.createElement('span');
    body.textContent = text;
    bubble.append(body);
    if (advice) {
      const adviceLine = document.createElement('p');
      adviceLine.className = 'message-advice';
      adviceLine.textContent = `조언 · ${advice}`;
      bubble.append(adviceLine);
    }
  }
  article.append(bubble);
  elements.chatLog.append(article);
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
  return article;
}

function resetChat() {
  elements.chatLog.replaceChildren();
  appendMessage({
    role: 'system',
    text: state.settings.mode === 'LOCAL_CODEX'
      ? 'Local Codex 모드입니다. 모델·추론 강도·해설 스타일을 조정한 뒤 질문과 카드 3장으로 실제 ChatGPT/Codex 구독 해석을 검증할 수 있습니다.'
      : '세 장의 카드와 질문을 정한 뒤 해석을 요청하세요. 기본값은 투자 질문 골든 테스트 사례입니다.',
  });
}

function setBusy(isBusy) {
  state.busy = isBusy;
  elements.submit.disabled = isBusy;
  elements.randomize.disabled = isBusy;
  elements.submit.querySelector('span').textContent = isBusy ? '요청 중' : '해석 요청';
}

function setConnectionStatus(status, label) {
  elements.connectionStatus.dataset.status = status;
  elements.connectionStatus.textContent = label;
}

function setLlmControlsEnabled() {
  const disabled = !elements.useLlm.checked;
  elements.llmModel.disabled = disabled;
  elements.llmReasoningEffort.disabled = disabled;
  elements.interpretationStyle.disabled = disabled;
}

function applyLocalCodexAiDefaults() {
  elements.useLlm.checked = true;
  elements.llmModel.value = 'gpt-5.6-sol';
  elements.llmReasoningEffort.value = 'XHIGH';
  elements.interpretationStyle.value = 'RICH';
  elements.responseLength.value = 'DETAILED';
  elements.includeTrace.checked = true;
  setLlmControlsEnabled();
}

function updateModeUi() {
  if (state.settings.mode === 'LOCAL_CODEX') {
    setConnectionStatus('online', 'Local Codex');
    elements.modeHint.textContent = '로컬 규칙 엔진 → 선택한 Codex 모델 → ChatGPT 구독으로 문장화합니다.';
    return;
  }
  if (state.settings.mode === 'REMOTE') {
    setConnectionStatus('online', '원격 API');
    elements.modeHint.textContent = `${state.settings.baseUrl}${state.settings.endpoint} 로 요청합니다.`;
    return;
  }
  setConnectionStatus('demo', '로컬 데모');
  elements.modeHint.textContent = '현재는 실제 API를 호출하지 않는 로컬 데모 모드입니다.';
}

function applyDialogModePreset() {
  if (elements.connectionMode.value !== 'LOCAL_CODEX') return;
  elements.baseUrl.value = LOCAL_CODEX_SETTINGS.baseUrl;
  elements.endpoint.value = LOCAL_CODEX_SETTINGS.endpoint;
  elements.healthPath.value = LOCAL_CODEX_SETTINGS.healthPath;
  elements.authMode.value = LOCAL_CODEX_SETTINGS.authMode;
  elements.token.value = '';
}

function syncDialogFromState() {
  elements.connectionMode.value = state.settings.mode;
  elements.baseUrl.value = state.settings.baseUrl;
  elements.endpoint.value = state.settings.endpoint;
  elements.healthPath.value = state.settings.healthPath;
  elements.authMode.value = state.settings.authMode;
  elements.token.value = state.token;
  elements.testResult.textContent = '';
  elements.testResult.className = 'connection-result';
  applyDialogModePreset();
}

function readDialogSettings() {
  if (elements.connectionMode.value === 'LOCAL_CODEX') {
    return { ...LOCAL_CODEX_SETTINGS };
  }
  return {
    mode: elements.connectionMode.value === 'REMOTE' ? 'REMOTE' : 'DEMO',
    baseUrl: elements.baseUrl.value.trim(),
    endpoint: elements.endpoint.value.trim() || '/api/consultation',
    healthPath: elements.healthPath.value.trim() || '/health',
    authMode: elements.authMode.value,
    timeoutMs: state.settings.timeoutMs,
  };
}

async function handleHealthCheck() {
  const candidate = readDialogSettings();
  elements.testConnection.disabled = true;
  elements.testResult.className = 'connection-result';
  elements.testResult.textContent = '연결을 확인하고 있습니다…';
  try {
    if (candidate.mode === 'DEMO') {
      elements.testResult.textContent = '로컬 데모 모드는 외부 연결 없이 동작합니다.';
      elements.testResult.classList.add('success');
      return;
    }
    const result = await checkHealth({
      baseUrl: candidate.baseUrl,
      healthPath: candidate.healthPath,
      authMode: candidate.authMode,
      token: elements.token.value,
      timeoutMs: 10000,
    });
    elements.testResult.textContent = candidate.mode === 'LOCAL_CODEX'
      ? `Local Codex 백엔드 연결 성공 · HTTP ${result.status}`
      : `연결 성공 · HTTP ${result.status}`;
    elements.testResult.classList.add('success');
  } catch (error) {
    elements.testResult.textContent = error instanceof Error ? error.message : String(error);
    elements.testResult.classList.add('error');
  } finally {
    elements.testConnection.disabled = false;
  }
}

function renderResponse(response) {
  const normalized = normalizeTarotResponse(response);
  const scoreLabel = normalized.score === null ? null : `점수 ${normalized.score.toFixed(2)}`;
  const tags = [
    { label: verdictLabel(normalized.verdict), variant: 'verdict' },
    ...(scoreLabel ? [{ label: scoreLabel }] : []),
    { label: normalized.llmUsed ? 'LLM 사용' : 'LLM 미사용' },
  ];
  if (normalized.llmUsed && normalized.llmModel) tags.push({ label: normalized.llmModel });
  if (normalized.llmUsed && normalized.llmReasoningEffort !== 'DEFAULT') {
    tags.push({ label: `Reasoning ${normalized.llmReasoningEffort}` });
  }
  if (normalized.llmUsed && normalized.interpretationStyle) {
    tags.push({ label: STYLE_LABELS[normalized.interpretationStyle] ?? normalized.interpretationStyle });
  }
  appendMessage({
    role: 'assistant',
    text: normalized.message || '응답 본문이 비어 있습니다. Response JSON을 확인하세요.',
    tags,
    flow: normalized.flowSummary,
    advice: normalized.advice,
  });
  elements.responseJson.textContent = pretty(normalized.raw);
  elements.traceJson.textContent = normalized.trace ? pretty(normalized.trace) : 'Trace가 없습니다.';
}

async function handleReadingSubmit(event) {
  event.preventDefault();
  if (state.busy) return;

  let payload;
  try {
    payload = buildConsultationPayload({
      question: elements.question.value,
      context: elements.additionalContext.value,
      readingContext: elements.readingContext.value,
      cards: selectedCards(),
      responseLength: elements.responseLength.value,
      includeTrace: elements.includeTrace.checked,
      useLlm: elements.useLlm.checked,
      llmModel: elements.llmModel.value,
      llmReasoningEffort: elements.llmReasoningEffort.value,
      interpretationStyle: elements.interpretationStyle.value,
    });
  } catch (error) {
    const message = error instanceof ReadingValidationError ? error.message : '입력값을 확인해 주세요.';
    appendMessage({ role: 'error', text: message });
    return;
  }

  elements.requestJson.textContent = pretty(payload);
  elements.responseJson.textContent = '응답을 기다리는 중…';
  elements.traceJson.textContent = 'Trace를 기다리는 중…';
  appendMessage({
    role: 'user',
    text: payload.question,
    meta: `YOU · ${cardSummary(payload.cards)}`,
  });
  const pending = appendMessage({ role: 'assistant', pending: true });
  setBusy(true);

  try {
    const response = state.settings.mode === 'DEMO'
      ? await runDemoConsultation(payload)
      : (await requestConsultation({
          baseUrl: state.settings.baseUrl,
          endpoint: state.settings.endpoint,
          payload,
          authMode: state.settings.authMode,
          token: state.token,
          timeoutMs: state.settings.timeoutMs,
        })).data;
    pending.remove();
    renderResponse(response);
    if (state.settings.mode === 'LOCAL_CODEX') setConnectionStatus('online', 'Local Codex 연결됨');
    if (state.settings.mode === 'REMOTE') setConnectionStatus('online', '원격 API 연결됨');
  } catch (error) {
    pending.remove();
    const message = error instanceof ApiRequestError
      ? `${error.message}${error.status ? ` (HTTP ${error.status})` : ''}`
      : error instanceof Error ? error.message : String(error);
    appendMessage({ role: 'error', text: message });
    elements.responseJson.textContent = pretty({
      error: error?.code ?? 'UNKNOWN_ERROR',
      message,
      status: error?.status ?? null,
      details: error?.details ?? null,
    });
    elements.traceJson.textContent = '요청 실패로 Trace가 없습니다.';
    setConnectionStatus('error', 'API 오류');
  } finally {
    setBusy(false);
  }
}

function randomIndex(max) {
  if (globalThis.crypto?.getRandomValues) {
    const value = new Uint32Array(1);
    globalThis.crypto.getRandomValues(value);
    return value[0] % max;
  }
  return Math.floor(Math.random() * max);
}

function randomizeCards() {
  const pool = [...TAROT_CARDS];
  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = randomIndex(i + 1);
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  pool.slice(0, 3).forEach((card, index) => {
    $(`card-${index + 1}`).value = card.code;
    $(`orientation-${index + 1}`).value = randomIndex(10) < 3 ? 'REVERSED' : 'UPRIGHT';
  });
}

async function copyInspector(targetId, button) {
  const text = $(targetId)?.textContent ?? '';
  try {
    await navigator.clipboard.writeText(text);
    const original = button.textContent;
    button.textContent = '복사됨';
    setTimeout(() => { button.textContent = original; }, 900);
  } catch {
    button.textContent = '복사 실패';
  }
}

function initialize() {
  [1, 2, 3].forEach((number) => populateCardSelect($(`card-${number}`)));
  $('card-1').value = 'TEN_OF_SWORDS';
  $('card-2').value = 'EIGHT_OF_WANDS';
  $('card-3').value = 'HIEROPHANT';

  if (state.settings.mode === 'LOCAL_CODEX') {
    applyLocalCodexAiDefaults();
  } else {
    setLlmControlsEnabled();
  }

  resetChat();
  updateModeUi();

  elements.form.addEventListener('submit', handleReadingSubmit);
  elements.randomize.addEventListener('click', randomizeCards);
  elements.clearChat.addEventListener('click', resetChat);
  elements.useLlm.addEventListener('change', setLlmControlsEnabled);

  elements.openSettings.addEventListener('click', () => {
    syncDialogFromState();
    elements.dialog.showModal();
  });
  elements.closeSettings.addEventListener('click', () => elements.dialog.close());
  elements.dialog.addEventListener('click', (event) => {
    if (event.target === elements.dialog) elements.dialog.close();
  });
  elements.connectionMode.addEventListener('change', applyDialogModePreset);
  elements.testConnection.addEventListener('click', handleHealthCheck);
  elements.settingsForm.addEventListener('submit', (event) => {
    event.preventDefault();
    state.settings = readDialogSettings();
    state.token = state.settings.mode === 'LOCAL_CODEX' ? '' : elements.token.value;
    persistSettings({ ...state.settings, token: state.token });
    if (state.settings.mode === 'LOCAL_CODEX') applyLocalCodexAiDefaults();
    updateModeUi();
    elements.dialog.close();
    appendMessage({
      role: 'system',
      text: state.settings.mode === 'LOCAL_CODEX'
        ? 'Local Codex 모드로 전환했습니다. GPT-5.6 Sol / XHigh / 풍부하게 / 상세하게를 기본값으로 적용했습니다.'
        : state.settings.mode === 'REMOTE'
          ? `원격 API 모드로 전환했습니다: ${state.settings.baseUrl}${state.settings.endpoint}`
          : '로컬 데모 모드로 전환했습니다.',
    });
  });

  document.querySelectorAll('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', (event) => {
      event.preventDefault();
      copyInspector(button.dataset.copyTarget, button);
    });
  });
}

initialize();
