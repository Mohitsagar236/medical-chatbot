import { useState, useRef } from 'react';
import { STRATEGIES } from '../../api/strategies';
import styles from './InputBar.module.css';

export default function InputBar({
  strategy,
  compareMode,
  loading,
  onStrategyChange,
  onToggleCompare,
  onStop,
  onSend,
  disabled,
}) {
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const textareaRef = useRef(null);

  const submit = async () => {
    const trimmed = text.trim();
    if (!trimmed) {
      setError('Enter a medical or biomedical question before sending.');
      return;
    }
    if (disabled) return;

    setError('');
    const ok = await onSend(trimmed);
    if (ok !== false) {
      setText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.focus();
      }
    }
  };

  const handleChange = (e) => {
    setText(e.target.value);
    if (error) setError('');
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 132)}px`;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className={styles.bar}>
      <div className={styles.inner}>
        <div className={styles.composerRow}>
          <label className={styles.selectorLabel} aria-label="Strategy">
            <select
              value={strategy.id}
              onChange={e => onStrategyChange(STRATEGIES.find(s => s.id === e.target.value))}
              disabled={compareMode || disabled}
            >
              {STRATEGIES.map(item => (
                <option key={item.id} value={item.id}>{item.label}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className={`${styles.compareToggle} ${compareMode ? styles.compareToggleActive : ''}`}
            onClick={onToggleCompare}
            disabled={disabled}
          >
            {compareMode ? 'Compare' : 'Single'}
          </button>
          <textarea
            ref={textareaRef}
            className={styles.input}
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a medical question..."
            disabled={disabled && !loading}
            rows={1}
            aria-label="Medical question"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'composer-error' : undefined}
          />
          {text && !loading && (
            <button type="button" className={styles.clearBtn} onClick={() => setText('')} aria-label="Clear input">
              Clear
            </button>
          )}
          {loading ? (
            <button
              type="button"
              className={styles.stopBtn}
              onClick={onStop}
              aria-label="Stop generation"
            >
              Stop
            </button>
          ) : (
            <button
              type="button"
              className={styles.sendBtn}
              onClick={submit}
              disabled={disabled || !text.trim()}
              aria-label="Generate answer"
              title="Generate answer"
            >
              <SendIcon />
            </button>
          )}
        </div>
        {error && <p id="composer-error" className={styles.error}>{error}</p>}
      </div>
    </div>
  );
}

function SendIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M22 2L11 13" />
      <path d="M22 2L15 22l-4-9-9-4 20-7z" />
    </svg>
  );
}
