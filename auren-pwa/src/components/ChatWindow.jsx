import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { useStore } from '../store';

export default function ChatWindow() {
  const messages = useStore((state) => state.messages);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  if (messages.length === 0) {
    return (
      <div className="chat-window">
        <div className="empty-state">
          <h3>Welcome to AUREN</h3>
          <p>Ask NEUROS about your biometrics, health optimization, or cognitive performance.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="chat-window">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
} 