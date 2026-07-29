import { STRATEGIES } from '../../api/strategies';
import styles from './WelcomePanel.module.css';

const SUGGESTED_QUESTIONS = [
  'What is hypertension?',
  'How is type 2 diabetes diagnosed?',
  'What are common causes of iron-deficiency anemia?',
  'Explain the difference between viral and bacterial infections.',
  'What recent evidence exists for hypertension treatment?',
];

export default function WelcomePanel({
  strategy,
  compareMode,
  onPromptSelect,
  onStrategyChange,
  onToggleCompare,
}) {
  return (
    <section className={styles.panel} aria-labelledby="welcome-title">
      <h2 id="welcome-title">Ask a clinical or biomedical question</h2>
      <p className={styles.copy}>
        Choose one strategy or compare all five AI approaches side by side.
      </p>

      <div className={styles.controls}>
        <label>
          <span>Strategy</span>
          <select value={strategy.id} onChange={e => onStrategyChange(STRATEGIES.find(s => s.id === e.target.value))}>
            {STRATEGIES.map(item => (
              <option key={item.id} value={item.id}>{item.label}</option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className={compareMode ? styles.activeToggle : styles.toggle}
          onClick={onToggleCompare}
        >
          {compareMode ? 'Compare Mode On' : 'Compare all strategies'}
        </button>
      </div>

      <div className={styles.suggestions} aria-label="Suggested questions">
        {SUGGESTED_QUESTIONS.map(question => (
          <button key={question} type="button" onClick={() => onPromptSelect(question)}>
            {question}
          </button>
        ))}
      </div>

      <p className={styles.disclaimer}>
        Educational information only. Not a substitute for professional medical advice.
      </p>
    </section>
  );
}
