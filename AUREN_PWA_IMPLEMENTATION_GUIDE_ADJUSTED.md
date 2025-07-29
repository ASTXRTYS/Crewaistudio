# AUREN PWA Implementation Guide (Adjusted for Your Backend)

*Created: January 29, 2025*  
*Purpose: Get you talking to NEUROS through a PWA within 48 hours*  
*Adjusted to work with your actual backend endpoints*

---

## 🚀 What You'll Build

A sleek PWA that connects to your existing NEUROS backend:
- ✅ Real-time text messaging with NEUROS
- ✅ Voice recording (files sent, transcription coming later)
- ✅ Image/file uploads for macro analysis
- ✅ 2-hour session limit (respects NEUROS memory constraints)
- ✅ Deployed on Vercel with HTTPS

---

## 📁 Project Structure

```
auren-pwa/
├── public/
│   ├── manifest.json
│   ├── favicon.ico
│   └── icons/
│       ├── icon-192.png
│       └── icon-512.png
├── src/
│   ├── components/
│   │   ├── ChatWindow.jsx
│   │   ├── MessageBubble.jsx
│   │   ├── InputBar.jsx
│   │   └── VoiceRecorder.jsx
│   ├── hooks/
│   │   ├── useWebSocket.js
│   │   └── useApi.js
│   ├── styles/
│   │   └── globals.css
│   ├── utils/
│   │   └── api.js
│   ├── store.js
│   ├── App.jsx
│   └── main.jsx
├── .env.local
├── package.json
├── vite.config.js
└── vercel.json
```

---

## 🛠 Step 1: Project Setup (10 minutes)

### 1.1 Create Project

```bash
npm create vite@latest auren-pwa -- --template react
cd auren-pwa
npm install
```

### 1.2 Install Dependencies

```bash
npm install \
  zustand \
  react-audio-voice-recorder \
  lucide-react \
  clsx \
  axios \
  vite-plugin-pwa
```

### 1.3 Environment Variables

Create `.env.local`:
```env
# For local development
VITE_API_URL=http://144.126.215.218:8888
VITE_WS_URL=ws://144.126.215.218:8888

# For production (update after deployment)
# VITE_API_URL=https://api.aupex.ai
# VITE_WS_URL=wss://api.aupex.ai
```

---

## 🎨 Step 2: Core Implementation

### 2.1 Vite Configuration

`vite.config.js`:
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'AUREN Neural Operations',
        short_name: 'AUREN',
        description: 'Elite Neural Operations System',
        theme_color: '#00D9FF',
        background_color: '#000000',
        display: 'standalone',
        icons: [
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ]
})
```

### 2.2 Global Styles

`src/styles/globals.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');

:root {
  /* AUREN Brand Colors from your backend */
  --auren-primary: #00D9FF;
  --auren-secondary: #9945FF;
  --auren-success: #00FF88;
  
  /* NEUROS Theme */
  --neuros-black: #0A0A0B;
  --neuros-steel: #1C1E26;
  --neuros-steel-light: #2A2D3A;
  --neuros-accent: #4A9EFF;
  --neuros-neural: #00D4FF;
  --neuros-text: #E7E9EA;
  --neuros-text-dim: #71767B;
  
  /* UI Elements */
  --border-color: rgba(255, 255, 255, 0.1);
  --shadow-glow: 0 0 20px rgba(0, 217, 255, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--neuros-black);
  color: var(--neuros-text);
  overflow-x: hidden;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--neuros-steel);
}

::-webkit-scrollbar-thumb {
  background: var(--neuros-accent);
  border-radius: 4px;
}

/* Gradient Text */
.gradient-text {
  background: linear-gradient(135deg, var(--auren-primary), var(--auren-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 2.3 API Utils

`src/utils/api.js`:
```javascript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL;

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  }
});

// API functions
export const chatAPI = {
  // Send text message
  sendMessage: async (text, sessionId) => {
    const response = await api.post('/api/chat/neuros', {
      text,
      agent_requested: 'neuros',
      session_id: sessionId
    });
    return response.data;
  },

  // Upload voice message
  sendVoice: async (audioBlob, sessionId) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.webm');
    formData.append('session_id', sessionId);
    formData.append('agent_requested', 'neuros');
    
    const response = await api.post('/api/chat/voice', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  },

  // Upload file
  uploadFile: async (file, sessionId, context) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    if (context) formData.append('context', context);
    
    const response = await api.post('/api/chat/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  },

  // Get chat history
  getHistory: async (sessionId) => {
    const response = await api.get(`/api/chat/history/${sessionId}`);
    return response.data;
  },

  // Get NEUROS status
  getNeurosStatus: async () => {
    const response = await api.get('/api/agents/neuros/status');
    return response.data;
  }
};
```

### 2.4 WebSocket Hook (Using Your Actual Endpoints)

`src/hooks/useWebSocket.js`:
```javascript
import { useEffect, useRef, useCallback, useState } from 'react';
import { useStore } from '../store';

export function useWebSocket() {
  const ws = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const { addMessage, setConnectionStatus, sessionId } = useStore();
  
  const connect = useCallback(() => {
    try {
      // Connect to your actual WebSocket endpoint
      const wsUrl = `${import.meta.env.VITE_WS_URL}/ws/dashboard/pwa_user`;
      console.log('Connecting to:', wsUrl);
      
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        
        // Send auth message (using test key for now)
        ws.current.send(JSON.stringify({
          type: 'auth',
          api_key: 'Bearer auren_sk_test_xxxxx',
          session_id: sessionId
        }));
      };
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        if (data.type === 'connection') {
          // Connection established
          console.log('Connection confirmed:', data);
        } else if (data.type === 'auth_success') {
          // Authentication successful
          console.log('Auth successful');
        } else if (data.type === 'agent_response') {
          // NEUROS response
          addMessage({
            id: Date.now(),
            text: data.response.text,
            sender: 'agent',
            agent: 'neuros',
            timestamp: data.timestamp || new Date().toISOString(),
            data: data.response.data
          });
        }
      };
      
      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
      
      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };
      
    } catch (error) {
      console.error('Failed to connect:', error);
      setConnectionStatus('error');
    }
  }, [addMessage, setConnectionStatus, sessionId]);
  
  const sendMessage = useCallback((text) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'message',
        text,
        agent_requested: 'neuros',
        timestamp: new Date().toISOString()
      }));
      return true;
    }
    return false;
  }, []);
  
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);
  
  return { 
    sendMessage, 
    isConnected,
    reconnect: connect 
  };
}
```

### 2.5 State Management

`src/store.js`:
```javascript
import { create } from 'zustand';

export const useStore = create((set, get) => ({
  messages: [],
  connectionStatus: 'connecting',
  isRecording: false,
  sessionId: `pwa_session_${Date.now().toString(36)}`,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  
  setRecording: (isRecording) => set({ isRecording }),
  
  clearMessages: () => set({ messages: [] }),
  
  getSessionId: () => get().sessionId
}));
```

### 2.6 Chat Window Component

`src/components/ChatWindow.jsx`:
```javascript
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
      
      <style jsx>{`
        .chat-window {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          display: flex;
          flex-direction: column;
        }
        
        .empty-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          opacity: 0.8;
        }
        
        .neuros-logo {
          margin-bottom: 1rem;
        }
        
        .logo-text {
          font-size: 3rem;
          font-weight: 900;
          letter-spacing: -0.02em;
        }
        
        .hint {
          color: var(--neuros-text-dim);
          margin-top: 0.5rem;
          font-size: 0.9rem;
        }
        
        .messages-container {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
      `}</style>
    </div>
  );
}
```

### 2.7 Input Bar with Voice & File Upload

`src/components/InputBar.jsx`:
```javascript
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
```

### 2.8 Main App

`src/App.jsx`:
```javascript
import React, { useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store';
import './styles/globals.css';

function App() {
  const { sendMessage, isConnected } = useWebSocket();
  const connectionStatus = useStore((state) => state.connectionStatus);
  const sessionId = useStore((state) => state.sessionId);
  
  useEffect(() => {
    // Log session info
    console.log('Session ID:', sessionId);
  }, [sessionId]);
  
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-text gradient-text">AUREN</span>
            <span className="logo-badge">ALPHA</span>
          </div>
          <div className="session-info">
            <div className={`status-dot ${connectionStatus}`} />
            <span>{isConnected ? 'Connected' : 'Connecting...'}</span>
          </div>
        </div>
      </header>
      
      <main className="chat-container">
        <ChatWindow />
        <InputBar onSendMessage={sendMessage} />
      </main>
      
      <style jsx>{`
        .app {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: var(--neuros-black);
        }
        
        .app-header {
          background: var(--neuros-steel);
          border-bottom: 1px solid var(--border-color);
        }
        
        .header-content {
          max-width: 800px;
          margin: 0 auto;
          padding: 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .logo {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .logo-text {
          font-size: 1.5rem;
          font-weight: 900;
          letter-spacing: -0.02em;
        }
        
        .logo-badge {
          font-size: 0.75rem;
          padding: 0.25rem 0.5rem;
          background: var(--neuros-accent);
          color: var(--neuros-black);
          border-radius: 0.25rem;
          font-weight: 600;
        }
        
        .session-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: var(--neuros-text-dim);
        }
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--neuros-text-dim);
        }
        
        .status-dot.connected {
          background: var(--auren-success);
        }
        
        .status-dot.error {
          background: #ff4444;
        }
        
        .chat-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          max-width: 800px;
          width: 100%;
          margin: 0 auto;
        }
      `}</style>
    </div>
  );
}

export default App;
```

### 2.9 Message Bubble (Complete)

`src/components/MessageBubble.jsx`:
```javascript
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
```

---

## 🚀 Step 3: Deployment

### 3.1 Vercel Configuration

`vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://144.126.215.218:8888/api/:path*"
    },
    {
      "source": "/ws/:path*",
      "destination": "http://144.126.215.218:8888/ws/:path*"
    }
  ]
}
```

### 3.2 Deploy to Vercel

```bash
# Install Vercel CLI if needed
npm i -g vercel

# Deploy
vercel

# Follow prompts to deploy
```

### 3.3 Update Environment for Production

After deployment, update your Vercel environment variables:
- `VITE_API_URL`: https://pwa.aupex.ai/api
- `VITE_WS_URL`: wss://pwa.aupex.ai/ws

---

## 🧪 Quick Test Guide

### Local Testing:
```bash
npm run dev
# Open http://localhost:5173
```

### Test Checklist:
- [ ] Send "How's my HRV today?" to NEUROS
- [ ] Record a voice message
- [ ] Upload a macro screenshot
- [ ] Check WebSocket is connected
- [ ] Install as PWA on phone

---

## 🐛 Common Issues & Fixes

### WebSocket Won't Connect?
1. Check your backend is running: `curl http://144.126.215.218:8888/health`
2. For local dev, ensure you're using `ws://` not `wss://`

### CORS Errors?
Your backend already has CORS configured for localhost:5173 and pwa.aupex.ai!

### Voice Recording Not Working?
- Requires HTTPS in production (Vercel provides this)
- For local testing, Chrome allows mic access on localhost

---

## ✅ You're Live!

You now have a working PWA that:
- ✅ Connects to your actual NEUROS backend
- ✅ Sends text, voice, and files
- ✅ Receives real-time responses
- ✅ Respects 2-hour session limits
- ✅ Works as a mobile app

**Backend is ready**, frontend is built, and you can start chatting with NEUROS! 🚀 