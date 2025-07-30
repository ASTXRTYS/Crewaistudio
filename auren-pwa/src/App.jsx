import { useState, useCallback, useEffect } from 'react';
import { chatAPI } from './utils/api';
import BiometricConnect from './components/BiometricConnect';
import NeurosChat from './components/NeurosChat';
import './App.css';
import './styles/BiometricConnect.css';

function App() {
  // Tab management state
  const [activeTab, setActiveTab] = useState('chat');
  
  // Existing NEUROS chat state - preserved completely
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: "Hello! I'm NEUROS, your neural optimization specialist. How can I help you today?", 
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [userId] = useState(() => `user_${Date.now()}`);

  // Monitor connection status
  useEffect(() => {
    const handleOnline = () => setIsConnected(true);
    const handleOffline = () => setIsConnected(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isLoading || !isConnected) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(inputMessage, sessionId);
      
      const aiMessage = {
        id: messages.length + 2,
        text: response.response || "I'm having trouble understanding. Could you rephrase that?",
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        id: messages.length + 2,
        text: "I'm having trouble connecting right now. Please check your internet connection and try again.",
        sender: 'assistant',
        timestamp: new Date(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputMessage, isLoading, isConnected, messages.length, sessionId]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const formatTime = useCallback((date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit' 
    });
  }, []);



  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>AUREN</h1>
          <span className="header-subtitle">AI Health Companion</span>
        </div>
        {!isConnected && (
          <div className="connection-status">
            <div className="offline-indicator" />
            Offline
          </div>
        )}
      </header>

      {/* Tab Navigation */}
      <div className="app-navigation">
        <button 
          className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <span>💬</span> NEUROS
        </button>
        <button 
          className={`nav-tab ${activeTab === 'devices' ? 'active' : ''}`}
          onClick={() => setActiveTab('devices')}
        >
          <span>⌚</span> Devices
        </button>
      </div>

      {/* Conditional rendering based on active tab */}
      {activeTab === 'chat' ? (
        <NeurosChat 
          key="neuros-chat"
          messages={messages}
          inputMessage={inputMessage}
          setInputMessage={setInputMessage}
          isLoading={isLoading}
          isConnected={isConnected}
          handleSendMessage={handleSendMessage}
          handleKeyPress={handleKeyPress}
          formatTime={formatTime}
        />
      ) : (
        <BiometricConnect key="biometric-connect" userId={userId} />
      )}
    </div>
  );
}

export default App;
