import styles from './Header.module.css';

export default function Header({
  onNewChat,
  compareMode,
  onToggleCompare,
  onToggleSidebar,
  onToggleTheme,
  themeLabel,
}) {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.topRow}>
          <div className={styles.brandGroup}>
            <button
              type="button"
              className={styles.menuBtn}
              onClick={onToggleSidebar}
              aria-label="Open menu"
            >
              <span />
              <span />
              <span />
            </button>
            <h1 className={styles.title}>MediQuery</h1>
            <p className={styles.descriptor}>Medical AI Strategy Comparison</p>
          </div>
          <div className={styles.headerActions}>
            <button
              type="button"
              className={styles.iconBtn}
              onClick={onToggleTheme}
              aria-label={`Theme: ${themeLabel}`}
              title={`Theme: ${themeLabel}`}
            >
              {themeLabel}
            </button>
            <button
              type="button"
              className={`${styles.compareBtn} ${compareMode ? styles.compareBtnActive : ''}`}
              onClick={onToggleCompare}
              title={compareMode ? 'Exit compare mode' : 'Compare all strategies side by side'}
            >
              {compareMode ? 'Exit Compare' : 'Compare All'}
            </button>
            <button
              type="button"
              className={styles.newChatBtn}
              onClick={onNewChat}
              title="Start a new conversation"
            >
              New Chat
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
