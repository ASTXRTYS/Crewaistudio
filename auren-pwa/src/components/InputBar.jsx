import React, { useState, useRef } from 'react';
import { Send, Paperclip, Mic, Square } from 'lucide-react';
// Removed audio recorder imports
import { useStore } from '../store';
import { chatAPI } from '../utils/api';

export default function InputBar({ onSendMessage }) {
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const { addMessage, sessionId } = useStore();
  
  const handleSend = async () => {
    if (input.trim()) {
      // Add user message to chat
      const userMessage = {
        id: Date.now(),
        text: input,
        sender: 'user',
        timestamp: new Date().toISOString()
      };
      
      addMessage(userMessage);
      
      // Send via WebSocket first (for real-time feel)
      const sent = onSendMessage(input);
      
      // Also send via REST API as backup
      if (!sent) {
        try {
          // Clear input immediately for better UX
          const messageText = input;
          setInput('');
          
          console.log('Sending via REST API...');
          const response = await chatAPI.sendMessage(messageText, sessionId);
          
          // Add NEUROS response
          const neurosMessage = {
            id: Date.now() + 1,
            text: response.response,
            sender: 'neuros',
            timestamp: response.timestamp || new Date().toISOString()
          };
          
          addMessage(neurosMessage);
        } catch (error) {
          console.error('Failed to send message:', error);
          // Show error message
          addMessage({
            id: Date.now() + 1,
            text: error.message || 'Failed to send message. Please check your connection.',
            sender: 'system',
            timestamp: new Date().toISOString()
          });
        }
      } else {
        setInput('');
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    
    try {
      // Add placeholder message
      addMessage({
        id: Date.now(),
        text: `Uploading ${file.name}...`,
        sender: 'system',
        timestamp: new Date().toISOString()
      });
      
      const response = await chatAPI.uploadFile(file, sessionId, input);
      
      // Add success message
      addMessage({
        id: Date.now() + 1,
        text: `File uploaded: ${file.name}`,
        sender: 'system',
        timestamp: new Date().toISOString()
      });
      
      // Add NEUROS response if any
      if (response.analysis) {
        addMessage({
          id: Date.now() + 2,
          text: response.analysis,
          sender: 'neuros',
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Upload failed:', error);
      addMessage({
        id: Date.now() + 1,
        text: 'File upload not yet implemented',
        sender: 'system',
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="input-bar">
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask NEUROS anything..."
          className="message-input"
        />
        
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          accept="image/*,.pdf,.txt,.csv"
        />
        
        <div className="input-actions">
          <button 
            className="icon-button"
            onClick={() => fileInputRef.current?.click()} 
            disabled={isUploading}
          >
            <Paperclip size={20} />
          </button>
          
          <button 
            className="send-button"
            onClick={handleSend}
            disabled={!input.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
} 