import { STRATEGIES } from '../../api/strategies';
import styles from './Sidebar.module.css';

export default function Sidebar({
  open,
  conversations,
  compareMode,
  onClose,
  onNewConversation,
  onToggleCompare,
}) {
  return (
    <>
      <aside className={`${styles.sidebar} ${open ? styles.open : ''}`} aria-label="Conversation sidebar">
        <div className={styles.mobileHeader}>
          <strong>MediQuery</strong>
          <button type="button" onClick={onClose} aria-label="Close sidebar">Close</button>
        </div>

        <button type="button" className={styles.primaryBtn} onClick={onNewConversation}>
          New Conversation
        </button>

        <label className={styles.searchLabel} htmlFor="conversation-search">Search conversations</label>
        <input
          id="conversation-search"
          className={styles.search}
          type="search"
          placeholder="Search local session"
          disabled
        />

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Recent</h2>
            <span>{conversations.length}</span>
          </div>
          {conversations.length === 0 ? (
            <p className={styles.empty}>Your successful questions will appear here during this session.</p>
          ) : (
            <ul className={styles.list}>
              {conversations.map(item => (
                <li key={item.id} className={styles.conversation}>
                  <span className={styles.conversationTitle}>{item.title}</span>
                  <span className={styles.conversationMeta}>{item.strategy} · {item.updatedAt}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Strategies</h2>
          </div>
          <div className={styles.strategyList}>
            {STRATEGIES.map(strategy => (
              <div key={strategy.id} className={styles.strategyItem}>
                <span className={`${styles.strategyDot} ${styles[strategy.accent]}`} />
                <div>
                  <strong>{strategy.label}</strong>
                  <p>{strategy.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <button
            type="button"
            className={`${styles.secondaryBtn} ${compareMode ? styles.secondaryActive : ''}`}
            onClick={onToggleCompare}
          >
            {compareMode ? 'Exit Compare Mode' : 'Open Compare Mode'}
          </button>
        </section>

        <p className={styles.methodology}>
          MediQuery compares response strategies for educational AI research. It is not a diagnostic tool.
        </p>
      </aside>
      {open && <button type="button" className={styles.backdrop} onClick={onClose} aria-label="Close sidebar" />}
    </>
  );
}
