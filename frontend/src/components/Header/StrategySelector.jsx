import { STRATEGIES } from '../../api/strategies';
import styles from './StrategySelector.module.css';

export default function StrategySelector({ strategy, onChange }) {
  return (
    <div className={styles.wrapper}>
      <label htmlFor="strategy-select" className={styles.label}>
        Strategy:
      </label>
      <select
        id="strategy-select"
        className={styles.select}
        value={strategy.id}
        onChange={e => onChange(STRATEGIES.find(s => s.id === e.target.value))}
      >
        {STRATEGIES.map(s => (
          <option key={s.id} value={s.id}>
            {s.label}
          </option>
        ))}
      </select>
    </div>
  );
}
