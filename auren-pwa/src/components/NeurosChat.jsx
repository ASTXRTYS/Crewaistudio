import React, { useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const NeurosChat = ({ 
  messages, 
  inputMessage, 
  setInputMessage, 
  isLoading, 
  isConnected, 
  handleSendMessage, 
  handleKeyPress,
  formatTime 
}) => {
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Maintain input focus
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <>
      {/* Messages Container */}
      <div className="messages-container">
        <div className="messages-scroll">
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.sender} ${message.isError ? 'error' : ''}`}
            >
              <div className="message-avatar">
                {message.sender === 'user' ? (
                  <User size={20} />
                ) : (
                  <Bot size={20} />
                )}
              </div>
              <div className="message-content">
                <div className="message-bubble">
                  {message.text}
                </div>
                <div className="message-time">
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">
                <Bot size={20} />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Container */}
      <div className="input-container">
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? "Ask NEUROS anything..." : "You're offline"}
            disabled={!isConnected}
            className="message-input"
            autoFocus
          />
          <button 
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading || !isConnected}
            className="send-button"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </div>
    </>
  );
};

export default React.memo(NeurosChat); 