const VERDICT_LABELS = {
  POSITIVE: '긍정',
  NEGATIVE: '부정',
  CAUTIOUS: '신중',
  DEMO: '데모',
  UNKNOWN: '미확인',
};

export function verdictLabel(verdict) {
  return VERDICT_LABELS[verdict] ?? verdict ?? VERDICT_LABELS.UNKNOWN;
}

export function normalizeTarotResponse(raw) {
  const source = raw && typeof raw === 'object' ? raw : { raw };
  const score = Number.isFinite(Number(source.score)) ? Number(source.score) : null;
  return {
    verdict: String(source.verdict ?? 'UNKNOWN').toUpperCase(),
    score,
    flowSummary: source.flow_summary ?? source.flowSummary ?? '',
    message: source.overall_interpretation ?? source.interpretation ?? source.response ?? source.message ?? '',
    advice: source.advice ?? '',
    cards: Array.isArray(source.cards) ? source.cards : [],
    trace: source.trace ?? null,
    llmUsed: Boolean(source.llm_used ?? source.llmUsed),
    llmModel: source.llm_model ?? source.llmModel ?? null,
    llmReasoningEffort: source.llm_reasoning_effort ?? source.llmReasoningEffort ?? 'DEFAULT',
    interpretationStyle: source.interpretation_style ?? source.interpretationStyle ?? 'BALANCED',
    disclaimer: source.disclaimer ?? '',
    raw: source,
  };
}
