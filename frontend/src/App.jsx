import { useEffect, useMemo, useState } from 'react';
import { useChat } from './hooks/useChat';
import { useCompare } from './hooks/useCompare';
import Header from './components/Header/Header';
import Sidebar from './components/Sidebar/Sidebar';
import ChatWindow from './components/Chat/ChatWindow';
import CompareView from './components/Compare/CompareView';
import InputBar from './components/InputBar/InputBar';
import styles from './App.module.css';

export default function App() {
  const [compareMode, setCompareMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('mediq-theme') || 'light');
  const [conversations, setConversations] = useState([]);
  const {
    strategy,
    messages,
    loading,
    handleSend,
    handleStop,
    handleNewChat,
    handleStrategyChange,
  } = useChat();
  const {
    columns,
    isAnyLoading,
    handleSend: handleCompareSend,
    handleStop: handleCompareStop,
    handleNewChat: handleCompareNewChat,
  } = useCompare();

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('mediq-theme', theme);
  }, [theme]);

  const activeLoading = compareMode ? isAnyLoading : loading;
  const activeStop = compareMode ? handleCompareStop : handleStop;
  const activeNewChat = compareMode ? handleCompareNewChat : handleNewChat;

  const recordConversation = (text) => {
    setConversations(prev => {
      const item = {
        id: crypto.randomUUID?.() || String(Date.now()),
        title: text,
        strategy: compareMode ? 'Compare Mode' : strategy.label,
        updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      return [item, ...prev].slice(0, 8);
    });
  };

  const sendSingle = async (text) => {
    const ok = await handleSend(text);
    if (ok) recordConversation(text);
    return ok;
  };

  const sendCompare = async (text) => {
    const ok = await handleCompareSend(text);
    if (ok) recordConversation(text);
    return ok;
  };

  const newConversation = () => {
    activeNewChat();
    setSidebarOpen(false);
  };

  const themeLabel = useMemo(() => {
    return theme === 'light' ? 'Light' : 'Dark';
  }, [theme]);

  const cycleTheme = () => {
    setTheme(current => current === 'light' ? 'dark' : 'light');
  };

  return (
    <div className={styles.app}>
      <Header
        strategy={strategy}
        onStrategyChange={handleStrategyChange}
        onNewChat={newConversation}
        compareMode={compareMode}
        onToggleCompare={() => setCompareMode(m => !m)}
        onToggleSidebar={() => setSidebarOpen(o => !o)}
        onToggleTheme={cycleTheme}
        themeLabel={themeLabel}
      />
      <div className={styles.shell}>
        <Sidebar
          open={sidebarOpen}
          conversations={conversations}
          compareMode={compareMode}
          onClose={() => setSidebarOpen(false)}
          onNewConversation={newConversation}
          onToggleCompare={() => setCompareMode(m => !m)}
        />
        <section className={styles.workspace}>
          {compareMode
            ? <CompareView columns={columns} />
            : (
              <ChatWindow
                messages={messages}
                loading={loading}
                strategy={strategy}
                compareMode={compareMode}
                onPromptSelect={sendSingle}
                onStrategyChange={handleStrategyChange}
                onToggleCompare={() => setCompareMode(m => !m)}
              />
            )
          }
          <InputBar
            strategy={strategy}
            compareMode={compareMode}
            loading={activeLoading}
            onStrategyChange={handleStrategyChange}
            onToggleCompare={() => setCompareMode(m => !m)}
            onStop={activeStop}
            onSend={compareMode ? sendCompare : sendSingle}
            disabled={activeLoading}
          />
        </section>
      </div>
    </div>
  );
}
