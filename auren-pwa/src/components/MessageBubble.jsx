import React from 'react';
import clsx from 'clsx';

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
      
      <style jsx>{`
        .message-wrapper {
          display: flex;
          margin-bottom: 0.5rem;
        }
        
        .message-wrapper.user {
          justify-content: flex-end;
        }
        
        .message-wrapper.agent {
          justify-content: flex-start;
        }
        
        .message-wrapper.system {
          justify-content: center;
        }
        
        .message-bubble {
          max-width: 70%;
          padding: 0.75rem 1rem;
          border-radius: 1rem;
          position: relative;
        }
        
        .user .message-bubble {
          background: linear-gradient(135deg, var(--neuros-accent), var(--auren-secondary));
          color: white;
        }
        
        .agent .message-bubble {
          background: var(--neuros-steel);
          border: 1px solid var(--border-color);
        }
        
        .system .message-bubble {
          background: transparent;
          border: 1px solid var(--border-color);
          color: var(--neuros-text-dim);
          font-size: 0.9rem;
        }
        
        .agent-label {
          font-size: 0.75rem;
          color: var(--neuros-accent);
          font-weight: 600;
          margin-bottom: 0.25rem;
        }
        
        .message-text {
          line-height: 1.5;
          word-wrap: break-word;
        }
        
        .message-data {
          margin-top: 0.5rem;
          padding: 0.5rem;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 0.5rem;
          font-family: monospace;
          font-size: 0.8rem;
          overflow-x: auto;
        }
        
        .message-time {
          font-size: 0.7rem;
          opacity: 0.7;
          margin-top: 0.25rem;
        }
      `}</style>
    </div>
  );
} 