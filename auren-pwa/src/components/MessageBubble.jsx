import React from 'react';

export default function MessageBubble({ message }) {
  const getMessageClass = () => {
    const baseClass = 'message';
    return `${baseClass} ${message.sender}`;
  };
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div className={getMessageClass()}>
      <div className="message-bubble">
        <p className="message-text">{message.text}</p>
        <span className="message-time">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
} 