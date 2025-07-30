import React, { useEffect, useState } from 'react';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store';
import './styles/globals.css';

function App() {
  const { sendMessage, isConnected } = useWebSocket();
  const connectionStatus = useStore((state) => state.connectionStatus);
  const sessionId = useStore((state) => state.sessionId);
  const messages = useStore((state) => state.messages);
  const [showAlert, setShowAlert] = useState(true);
  
  // Check if we're on HTTPS and need to show mixed content warning
  const isHTTPS = window.location.protocol === 'https:';
  
  useEffect(() => {
    // Log session info
    console.log('Session ID:', sessionId);
  }, [sessionId]);
  
  // Check for network errors in messages
  const hasNetworkError = messages.some(msg => 
    msg.sender === 'system' && msg.text.includes('Network error')
  );
  
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-text gradient-text">AUREN</span>
            <span className="logo-badge">ALPHA</span>
          </div>
          <div className="session-info">
            <div className={`status-dot ${isHTTPS ? 'connected' : connectionStatus}`} />
            <span>{isHTTPS ? 'REST API Mode' : (isConnected ? 'Connected' : 'Connecting...')}</span>
          </div>
        </div>
      </header>
      
      <main className="chat-container">
        {isHTTPS && showAlert && (
          <div className="network-alert">
            <div className="alert-content">
              <strong>Network error - Please allow mixed content in your browser settings</strong>
              <span>(click lock icon → Site settings → Insecure content → Allow)</span>
            </div>
            <div className="alert-time">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
          </div>
        )}
        <ChatWindow />
        <div className="status-bar">
          <span className="status-text">ask NEUROS anything</span>
        </div>
        <InputBar onSendMessage={sendMessage} />
      </main>
    </div>
  );
}

export default App;
