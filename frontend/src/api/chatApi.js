async function postJSON(url, body, options = {}) {
  const startedAt = performance.now();
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message = err.detail || `Request failed with status ${res.status}`;
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }

  const data = await res.json();
  return {
    ...data,
    latency_ms: Math.round(performance.now() - startedAt),
  };
}

export async function sendMessage({ strategy, query, sessionId, topK = 5, signal }) {
  const { id, endpoint } = strategy;

  const bodyByStrategy = {
    S1: { query },
    S2: { query, top_k: topK },
    S3: { session_id: sessionId, query },
    S4: { session_id: sessionId, query, top_k: topK },
    S5: { query, top_k: topK },
  };

  return postJSON(endpoint, bodyByStrategy[id], { signal });
}

export async function clearSession(strategy, sessionId) {
  if (!strategy.hasMemory) return;

  const baseByStrategy = {
    S3: '/api/v1/chat/multi-turn-llm',
    S4: '/api/v1/chat/multi-turn-rag',
  };

  const base = baseByStrategy[strategy.id];
  if (!base) return;

  await fetch(`${base}/${sessionId}`, { method: 'DELETE' }).catch(() => {});
}
