import { useEffect, useRef } from 'react';
import EmergencyNotice, { hasUrgentLanguage } from './EmergencyNotice';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import WelcomePanel from './WelcomePanel';
import styles from './ChatWindow.module.css';

export default function ChatWindow({
  messages,
  loading,
  strategy,
  compareMode,
  onPromptSelect,
  onStrategyChange,
  onToggleCompare,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <main className={styles.window} aria-live="polite" aria-label="Chat messages">
      {messages.length === 0 && !loading && (
        <div className={styles.empty}>
          <WelcomePanel
            strategy={strategy}
            compareMode={compareMode}
            onPromptSelect={onPromptSelect}
            onStrategyChange={onStrategyChange}
            onToggleCompare={onToggleCompare}
          />
        </div>
      )}

      {messages.length > 0 && hasUrgentLanguage(messages) && <EmergencyNotice />}

      {messages.map((msg, i) => (
        <MessageBubble key={i} message={msg} />
      ))}

      {loading && <TypingIndicator />}

      <div ref={bottomRef} />
    </main>
  );
}
