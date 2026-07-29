import { useState } from 'react';
import Avatar from './Avatar';
import SourceChunks from './SourceChunks';
import styles from './MessageBubble.module.css';

export default function MessageBubble({ message }) {
  const { role, content, chunks, toolCalls, isError, cancelled, meta } = message;
  const [copyState, setCopyState] = useState('Copy');
  const [feedback, setFeedback] = useState('');
  const isUser = role === 'user';
  const hasMeta = !isUser && meta && (meta.strategy || meta.model || meta.historyLength);
  const isAgent = !isUser && toolCalls && toolCalls.length > 0;

  const copyAnswer = async () => {
    await navigator.clipboard?.writeText(content);
    setCopyState('Copied');
    window.setTimeout(() => setCopyState('Copy'), 1400);
  };

  return (
    <div className={`${styles.row} ${isUser ? styles.userRow : styles.assistantRow}`}>
      {!isUser && <Avatar role="assistant" />}

      <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.assistantBubble} ${isError ? styles.errorBubble : ''}`}>
        {isError && <div className={styles.errorLabel}>{cancelled ? 'Cancelled' : 'Request failed'}</div>}
        {!isUser && !isError && <div className={styles.aiLabel}>AI-generated educational response</div>}
        <p className={styles.text}>{content}</p>
        {hasMeta && (
          <div className={styles.meta}>
            {meta.strategyLabel && <span>{meta.strategyLabel}</span>}
            {meta.strategy && <span>{meta.strategy}</span>}
            {meta.model && <span>{meta.model}</span>}
            {meta.historyLength && <span>{meta.historyLength} turn{meta.historyLength === 1 ? '' : 's'}</span>}
            {meta.latencyMs && <span>{(meta.latencyMs / 1000).toFixed(1)}s</span>}
            {meta.usesMemory && <span>Memory enabled</span>}
            {meta.usesRAG && <span>Retrieval enabled</span>}
          </div>
        )}
        {isAgent && (
          <details className={styles.agentPanel}>
            <summary>Agent activity</summary>
            <ul>
              {toolCalls.map((call, index) => (
                <li key={`${call.query}-${index}`}>
                  Searched PubMed for "{call.query}" and found {call.chunks_found} chunk{call.chunks_found === 1 ? '' : 's'}.
                </li>
              ))}
            </ul>
          </details>
        )}
        {!isUser && <SourceChunks chunks={chunks} showEmpty={meta?.usesRAG} />}
        {!isUser && (
          <div className={styles.actions}>
            <button type="button" onClick={copyAnswer}>{copyState}</button>
            <button type="button" className={feedback === 'helpful' ? styles.activeAction : ''} onClick={() => setFeedback('helpful')}>
              Helpful
            </button>
            <button type="button" className={feedback === 'missing-evidence' ? styles.activeAction : ''} onClick={() => setFeedback('missing-evidence')}>
              Missing evidence
            </button>
          </div>
        )}
      </div>

      {isUser && <Avatar role="user" />}
    </div>
  );
}
