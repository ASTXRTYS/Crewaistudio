import React, { useState, useRef } from 'react';
import { Send, Paperclip, Mic, Square } from 'lucide-react';
import { AudioRecorder } from 'react-audio-voice-recorder';
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
          await chatAPI.sendMessage(input, sessionId);
        } catch (error) {
          console.error('Failed to send message:', error);
        }
      }
      
      setInput('');
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  const handleAudioStop = async (audioBlob) => {
    // Add voice message indicator
    const voiceMessage = {
      id: Date.now(),
      text: '🎤 Sending voice message...',
      sender: 'user',
      timestamp: new Date().toISOString(),
      isVoice: true
    };
    
    addMessage(voiceMessage);
    
    try {
      const response = await chatAPI.sendVoice(audioBlob, sessionId);
      console.log('Voice upload response:', response);
      
      // Update message
      voiceMessage.text = '🎤 Voice message sent (transcription coming soon)';
    } catch (error) {
      console.error('Failed to upload voice:', error);
      voiceMessage.text = '❌ Failed to send voice message';
    }
  };
  
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file && !isUploading) {
      setIsUploading(true);
      
      // Determine context based on file type
      let context = 'general';
      if (file.type.startsWith('image/')) {
        context = 'nutrition_tracking'; // Assume images are macro screenshots
      }
      
      // Add upload message
      const uploadMessage = {
        id: Date.now(),
        text: `📎 Uploading ${file.name}...`,
        sender: 'user',
        timestamp: new Date().toISOString(),
        isFile: true
      };
      
      addMessage(uploadMessage);
      
      try {
        const response = await chatAPI.uploadFile(file, sessionId, context);
        console.log('File upload response:', response);
        
        // Update message
        uploadMessage.text = `📎 ${file.name} uploaded successfully`;
        
        // Add system message about analysis
        addMessage({
          id: Date.now() + 1,
          text: `Analyzing your ${context.replace('_', ' ')}...`,
          sender: 'system',
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('Failed to upload file:', error);
        uploadMessage.text = `❌ Failed to upload ${file.name}`;
      } finally {
        setIsUploading(false);
      }
    }
  };
  
  return (
    <div className="input-bar">
      <button
        className="icon-button"
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
      >
        <Paperclip size={20} />
      </button>
      
      <input
        ref={fileInputRef}
        type="file"
        hidden
        onChange={handleFileUpload}
        accept="image/*,.pdf,.doc,.docx"
      />
      
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Ask NEUROS about your biometrics..."
        className="message-input"
        rows={1}
      />
      
      {input.trim() ? (
        <button className="send-button" onClick={handleSend}>
          <Send size={20} />
        </button>
      ) : (
        <div className="audio-recorder-wrapper">
          <AudioRecorder
            onRecordingComplete={handleAudioStop}
            audioTrackConstraints={{
              noiseSuppression: true,
              echoCancellation: true,
            }}
            showVisualizer={false}
          />
        </div>
      )}
      
      <style jsx>{`
        .input-bar {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 1rem;
          background: var(--neuros-steel);
          border-top: 1px solid var(--border-color);
        }
        
        .message-input {
          flex: 1;
          background: var(--neuros-black);
          border: 1px solid var(--border-color);
          border-radius: 1rem;
          padding: 0.75rem 1rem;
          color: var(--neuros-text);
          font-family: inherit;
          resize: none;
          outline: none;
          transition: border-color 0.2s;
        }
        
        .message-input:focus {
          border-color: var(--neuros-accent);
        }
        
        .icon-button,
        .send-button {
          background: none;
          border: none;
          color: var(--neuros-text-dim);
          cursor: pointer;
          padding: 0.5rem;
          border-radius: 0.5rem;
          transition: all 0.2s;
        }
        
        .icon-button:hover:not(:disabled),
        .send-button:hover {
          color: var(--neuros-accent);
          background: rgba(74, 158, 255, 0.1);
        }
        
        .icon-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .send-button {
          color: var(--neuros-accent);
        }
        
        .audio-recorder-wrapper {
          display: flex;
          align-items: center;
        }
        
        /* Override audio recorder styles */
        .audio-recorder-wrapper :global(.audio-recorder) {
          background: transparent !important;
        }
        
        .audio-recorder-wrapper :global(.audio-recorder-mic) {
          background: var(--neuros-accent) !important;
          border: none !important;
        }
      `}</style>
    </div>
  );
} 