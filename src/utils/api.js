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