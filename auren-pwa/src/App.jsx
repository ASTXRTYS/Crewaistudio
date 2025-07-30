import React, { useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store';
import './styles/globals.css';

function App() {
  const { sendMessage, isConnected } = useWebSocket();
  const connectionStatus = useStore((state) => state.connectionStatus);
  const sessionId = useStore((state) => state.sessionId);
  
  useEffect(() => {
    // Log session info
    console.log('Session ID:', sessionId);
  }, [sessionId]);
  
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-text gradient-text">AUREN</span>
            <span className="logo-badge">ALPHA</span>
          </div>
          <div className="session-info">
            <div className={`status-dot ${connectionStatus}`} />
            <span>{isConnected ? 'Connected' : 'Connecting...'}</span>
          </div>
        </div>
      </header>
      
      <main className="chat-container">
        <ChatWindow />
        <InputBar onSendMessage={sendMessage} />
      </main>
      
      <style jsx>{`
        .app {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: var(--neuros-black);
        }
        
        .app-header {
          background: var(--neuros-steel);
          border-bottom: 1px solid var(--border-color);
        }
        
        .header-content {
          max-width: 800px;
          margin: 0 auto;
          padding: 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .logo {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .logo-text {
          font-size: 1.5rem;
          font-weight: 900;
          letter-spacing: -0.02em;
        }
        
        .logo-badge {
          font-size: 0.75rem;
          padding: 0.25rem 0.5rem;
          background: var(--neuros-accent);
          color: var(--neuros-black);
          border-radius: 0.25rem;
          font-weight: 600;
        }
        
        .session-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: var(--neuros-text-dim);
        }
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--neuros-text-dim);
        }
        
        .status-dot.connected {
          background: var(--auren-success);
        }
        
        .status-dot.error {
          background: #ff4444;
        }
        
        .chat-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          max-width: 800px;
          width: 100%;
          margin: 0 auto;
        }
      `}</style>
    </div>
  );
}

export default App;
