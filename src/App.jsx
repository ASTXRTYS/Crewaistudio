import React, { useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store';
import './App.css';

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
    </div>
  );
}

export default App; 