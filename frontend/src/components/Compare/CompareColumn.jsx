import { useEffect, useRef } from 'react';
import MessageBubble from '../Chat/MessageBubble';
import TypingIndicator from '../Chat/TypingIndicator';
import styles from './CompareColumn.module.css';

export default function CompareColumn({ strategy, messages, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className={styles.column}>
      <div className={styles.columnHeader}>
        <div>
          <span className={styles.label}>{strategy.label}</span>
          <p className={styles.description}>{strategy.description}</p>
        </div>
        <div className={styles.badges}>
          <span className={`${styles.badge} ${strategy.hasRAG ? styles.badgeOn : styles.badgeOff}`}>
            RAG
          </span>
          <span className={`${styles.badge} ${strategy.hasMemory ? styles.badgeOn : styles.badgeOff}`}>
            Memory
          </span>
        </div>
      </div>

      <div className={styles.messages}>
        {messages.length === 0 && !loading && (
          <p className={styles.empty}>Awaiting query...</p>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
