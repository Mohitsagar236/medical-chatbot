import styles from './EmergencyNotice.module.css';

const URGENT_PATTERN = /\b(chest pain|can't breathe|cannot breathe|suicidal|overdose|stroke|severe bleeding|unconscious|heart attack)\b/i;

export function hasUrgentLanguage(messages) {
  const lastUserMessage = [...messages].reverse().find(message => message.role === 'user');
  return Boolean(lastUserMessage && URGENT_PATTERN.test(lastUserMessage.content));
}

export default function EmergencyNotice() {
  return (
    <div className={styles.notice} role="note">
      <strong>Possible urgent concern</strong>
      <span>
        If this may be an emergency, contact local emergency services or a qualified healthcare professional now.
      </span>
    </div>
  );
}
