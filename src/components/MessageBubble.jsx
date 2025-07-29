import React from 'react';
import clsx from 'clsx';
import './MessageBubble.css';

export default function MessageBubble({ message }) {
  const isUser = message.sender === 'user';
  const isAgent = message.sender === 'agent';
  const isSystem = message.sender === 'system';
  
  return (
    <div className={clsx('message-wrapper', message.sender)}>
      <div className="message-bubble">
        {isAgent && (
          <div className="agent-label">
            NEUROS
          </div>
        )}
        <div className="message-text">{message.text}</div>
        {message.data && (
          <div className="message-data">
            {JSON.stringify(message.data, null, 2)}
          </div>
        )}
        <div className="message-time">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  );
} 