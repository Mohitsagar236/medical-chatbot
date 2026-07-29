import { useState, useCallback, useRef } from 'react';
import { DEFAULT_STRATEGY, makeSessionId } from '../api/strategies';
import { sendMessage, clearSession } from '../api/chatApi';

export function useChat() {
  const [strategy, setStrategy] = useState(DEFAULT_STRATEGY);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const sessionIdRef = useRef(makeSessionId());
  const abortRef = useRef(null);
  const lastPromptRef = useRef('');

  const resetSession = useCallback(async (currentStrategy, currentMessages) => {
    if (currentStrategy.hasMemory && currentMessages.length > 0) {
      await clearSession(currentStrategy, sessionIdRef.current);
    }
    sessionIdRef.current = makeSessionId();
    setMessages([]);
  }, []);

  const handleNewChat = useCallback(() => {
    resetSession(strategy, messages);
  }, [strategy, messages, resetSession]);

  const handleStrategyChange = useCallback(async (newStrategy) => {
    await resetSession(strategy, messages);
    setStrategy(newStrategy);
  }, [strategy, messages, resetSession]);

  const handleSend = useCallback(async (text) => {
    if (!text.trim() || loading) return;

    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    lastPromptRef.current = text;
    abortRef.current = new AbortController();

    try {
      const data = await sendMessage({
        strategy,
        query: text,
        sessionId: sessionIdRef.current,
        signal: abortRef.current.signal,
      });

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          chunks: data.retrieved_chunks ?? [],
          toolCalls: data.tool_calls ?? [],
          meta: {
            strategy: data.strategy,
            model: data.model,
            historyLength: data.history_length,
            latencyMs: data.latency_ms,
            usesRAG: strategy.hasRAG,
            usesMemory: strategy.hasMemory,
            strategyLabel: strategy.label,
          },
        },
      ]);
      return true;
    } catch (err) {
      const wasAborted = err.name === 'AbortError';
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: wasAborted ? 'Request cancelled.' : err.message,
          isError: true,
          cancelled: wasAborted,
          meta: {
            strategyLabel: strategy.label,
          },
        },
      ]);
      return false;
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [strategy, loading]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    strategy,
    messages,
    loading,
    handleSend,
    handleNewChat,
    handleStrategyChange,
    handleStop,
    lastPrompt: lastPromptRef.current,
  };
}
