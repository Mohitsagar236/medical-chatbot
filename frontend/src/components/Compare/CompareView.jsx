import { STRATEGIES } from '../../api/strategies';
import CompareColumn from './CompareColumn';
import styles from './CompareView.module.css';

export default function CompareView({ columns }) {
  const stats = STRATEGIES.reduce((acc, strategy) => {
    const assistantMessages = columns[strategy.id].messages.filter(message => message.role === 'assistant');
    const latest = assistantMessages[assistantMessages.length - 1];
    if (!latest) return acc;
    if (latest.isError) acc.failed += 1;
    else acc.completed += 1;
    acc.sources += latest.chunks?.length || 0;
    if (latest.meta?.latencyMs && (!acc.fastest || latest.meta.latencyMs < acc.fastest.latencyMs)) {
      acc.fastest = { label: strategy.label, latencyMs: latest.meta.latencyMs };
    }
    if (strategy.hasRAG) acc.retrieval += 1;
    if (strategy.hasMemory) acc.memory += 1;
    return acc;
  }, { completed: 0, failed: 0, sources: 0, fastest: null, retrieval: 0, memory: 0 });

  return (
    <div className={styles.workspace}>
      <section className={styles.summary} aria-label="Comparison summary">
        <div><strong>{stats.completed}</strong><span>completed</span></div>
        <div><strong>{stats.failed}</strong><span>failed</span></div>
        <div><strong>{stats.sources}</strong><span>sources returned</span></div>
        <div><strong>{stats.fastest ? `${(stats.fastest.latencyMs / 1000).toFixed(1)}s` : '-'}</strong><span>fastest response</span></div>
        <div><strong>{stats.retrieval}</strong><span>retrieval-enabled</span></div>
        <div><strong>{stats.memory}</strong><span>memory-enabled</span></div>
      </section>
      <div className={styles.grid}>
        {STRATEGIES.map(strategy => (
          <CompareColumn
            key={strategy.id}
            strategy={strategy}
            messages={columns[strategy.id].messages}
            loading={columns[strategy.id].loading}
          />
        ))}
      </div>
    </div>
  );
}
