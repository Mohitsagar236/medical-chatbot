import { useState } from 'react';
import styles from './SourceChunks.module.css';

export default function SourceChunks({ chunks, showEmpty = false }) {
  const [open, setOpen] = useState(false);

  if (!chunks || chunks.length === 0) {
    if (!showEmpty) return null;
    return (
      <div className={styles.emptySources}>
        No external sources were returned for this response.
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={styles.toggle}
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <span className={styles.icon}>{open ? '-' : '+'}</span>
        {chunks.length} source{chunks.length !== 1 ? 's' : ''} retrieved
      </button>

      {open && (
        <ul className={styles.list}>
          {chunks.map((chunk, i) => (
            <li key={i} className={styles.chunk}>
              <div className={styles.chunkHeader}>
                <a
                  className={styles.source}
                  href={`https://pubmed.ncbi.nlm.nih.gov/${chunk.source}/`}
                  target="_blank"
                  rel="noreferrer"
                >
                  PubMed {chunk.source}
                </a>
                <span className={styles.score}>{(chunk.score * 100).toFixed(0)}% match</span>
              </div>
              <p className={styles.content}>{chunk.content}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
