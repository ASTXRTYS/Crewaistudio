import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { useStore } from '../store';
import './ChatWindow.css';

export default function ChatWindow() {
  const messages = useStore((state) => state.messages);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="neuros-logo">
            <span className="logo-text gradient-text">NEUROS</span>
          </div>
          <p>Elite Neural Operations System</p>
          <p className="hint">Ask about your HRV, recovery, or upload macro screenshots</p>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
} 