import axios from 'axios';

// Use proxy paths for production, direct URLs for development
const API_BASE = import.meta.env.VITE_API_URL || '/api/biometric';
const NEUROS_BASE = import.meta.env.VITE_NEUROS_URL || '/api/neuros';

// Create axios instances
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  }
});

const neurosApi = axios.create({
  baseURL: NEUROS_BASE,
  headers: {
    'Content-Type': 'application/json',
  }
});

// API functions
export const chatAPI = {
  // Send text message to NEUROS (using the correct endpoint)
  sendMessage: async (text, sessionId) => {
    try {
      // REST API call through Vercel proxy
      console.log('Sending via REST API to NEUROS through proxy...');
      const response = await neurosApi.post('/api/agents/neuros/analyze', {
        message: text,
        session_id: sessionId,
        user_id: sessionId, // Using session as user ID for now
        context: { source: 'pwa' }
      });
      
      // Extract the response text from NEUROS format
      return {
        response: response.data.response || response.data.analysis || response.data.message || 'No response from NEUROS',
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error sending message:', error);
      throw new Error(`Communication error: ${error.message}`);
    }
  },

  // Voice messages not yet implemented in NEUROS
  sendVoice: async (audioBlob, sessionId) => {
    throw new Error('Voice messages not yet implemented. Please use text messages.');
  },

  // File upload not yet implemented
  uploadFile: async (file, sessionId, context) => {
    throw new Error('File upload not yet implemented.');
  },

  // Get chat history - using local storage for now
  getHistory: async (sessionId) => {
    // Return empty history for now as NEUROS doesn't have a history endpoint
    return {
      messages: [],
      session_id: sessionId
    };
  },

  // Get NEUROS status
  getNeurosStatus: async () => {
    try {
      const response = await neurosApi.get('/health');
      return {
        status: response.data.status,
        service: response.data.service || 'NEUROS Advanced Reasoning'
      };
    } catch (error) {
      console.error('Error fetching NEUROS status:', error);
      return {
        status: 'error',
        service: 'NEUROS (unreachable)'
      };
    }
  }
};
