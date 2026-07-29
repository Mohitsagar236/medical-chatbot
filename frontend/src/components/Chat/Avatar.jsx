import styles from './Avatar.module.css';

export default function Avatar({ role }) {
  return (
    <div
      className={`${styles.avatar} ${role === 'user' ? styles.user : styles.assistant}`}
      aria-hidden="true"
    >
      {role === 'user' ? 'U' : 'AI'}
    </div>
  );
}
