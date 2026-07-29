export const STRATEGIES = [
  {
    id: 'S1',
    label: 'S1 - Simple LLM',
    description: 'No RAG, no memory',
    capabilities: ['LLM', 'Fast response', 'Model knowledge'],
    accent: 'llm',
    endpoint: '/api/v1/chat/single-llm/',
    hasMemory: false,
    hasRAG: false,
  },
  {
    id: 'S2',
    label: 'S2 - Single RAG',
    description: 'With RAG, no memory',
    capabilities: ['LLM', 'PubMed retrieval', 'Sources'],
    accent: 'rag',
    endpoint: '/api/v1/chat/single-rag/',
    hasMemory: false,
    hasRAG: true,
  },
  {
    id: 'S3',
    label: 'S3 - Multi-Turn LLM',
    description: 'No RAG, with memory',
    capabilities: ['LLM', 'Conversation memory', 'Follow-ups'],
    accent: 'memory',
    endpoint: '/api/v1/chat/multi-turn-llm/',
    hasMemory: true,
    hasRAG: false,
  },
  {
    id: 'S4',
    label: 'S4 - Multi-Turn RAG',
    description: 'With RAG + memory',
    capabilities: ['LLM', 'PubMed retrieval', 'Memory', 'Sources'],
    accent: 'hybrid',
    endpoint: '/api/v1/chat/multi-turn-rag/',
    hasMemory: true,
    hasRAG: true,
  },
  {
    id: 'S5',
    label: 'S5 - Agent RAG',
    description: 'Agentic tool-use, dynamic retrieval',
    capabilities: ['LLM', 'Agent tools', 'PubMed retrieval', 'Sources'],
    accent: 'agent',
    endpoint: '/api/v1/chat/agent-rag/',
    hasMemory: false,
    hasRAG: true,
  },
];

export const DEFAULT_STRATEGY = STRATEGIES[0];

export function makeSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}
