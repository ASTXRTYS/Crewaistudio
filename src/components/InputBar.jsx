import React, { useState, useRef } from 'react';
import { Send, Paperclip, Mic, Square } from 'lucide-react';
import { AudioRecorder } from 'react-audio-voice-recorder';
import { useStore } from '../store';
import { chatAPI } from '../utils/api';
import './InputBar.css';

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
        e.target.value = null; // Reset file input
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
    </div>
  );
} 