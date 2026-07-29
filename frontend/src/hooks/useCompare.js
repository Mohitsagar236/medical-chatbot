import { useState, useCallback, useRef } from 'react';
import { STRATEGIES, makeSessionId } from '../api/strategies';
import { sendMessage, clearSession } from '../api/chatApi';

const makeInitialColumns = () =>
  Object.fromEntries(STRATEGIES.map(s => [s.id, { messages: [], loading: false }]));

export function useCompare() {
  const [columns, setColumns] = useState(makeInitialColumns);
  const sessionIds = useRef(Object.fromEntries(STRATEGIES.map(s => [s.id, makeSessionId()])));
  const isLoadingRef = useRef(false);
  const abortControllersRef = useRef({});

  const handleSend = useCallback(async (text) => {
    if (!text.trim() || isLoadingRef.current) return;
    isLoadingRef.current = true;
    abortControllersRef.current = {};

    const userMessage = { role: 'user', content: text };

    setColumns(prev =>
      Object.fromEntries(
        STRATEGIES.map(s => [
          s.id,
          { messages: [...prev[s.id].messages, userMessage], loading: true },
        ])
      )
    );

    await Promise.allSettled(
      STRATEGIES.map(async (strategy) => {
        try {
          const controller = new AbortController();
          abortControllersRef.current[strategy.id] = controller;
          const data = await sendMessage({
            strategy,
            query: text,
            sessionId: sessionIds.current[strategy.id],
            signal: controller.signal,
          });

          setColumns(prev => ({
            ...prev,
            [strategy.id]: {
              loading: false,
              messages: [
                ...prev[strategy.id].messages,
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
              ],
            },
          }));
        } catch (err) {
          const wasAborted = err.name === 'AbortError';
          setColumns(prev => ({
            ...prev,
            [strategy.id]: {
              loading: false,
              messages: [
                ...prev[strategy.id].messages,
                {
                  role: 'assistant',
                  content: wasAborted ? 'Request cancelled.' : err.message,
                  isError: true,
                  cancelled: wasAborted,
                  meta: {
                    strategyLabel: strategy.label,
                  },
                },
              ],
            },
          }));
        }
      })
    );

    isLoadingRef.current = false;
    abortControllersRef.current = {};
    return true;
  }, []);

  const handleNewChat = useCallback(() => {
    STRATEGIES.forEach(s => {
      if (s.hasMemory) {
        clearSession(s, sessionIds.current[s.id]).catch(() => {});
      }
      sessionIds.current[s.id] = makeSessionId();
    });
    setColumns(makeInitialColumns());
  }, []);

  const isAnyLoading = Object.values(columns).some(c => c.loading);
  const handleStop = useCallback(() => {
    Object.values(abortControllersRef.current).forEach(controller => controller.abort());
  }, []);

  return { columns, isAnyLoading, handleSend, handleNewChat, handleStop };
}
