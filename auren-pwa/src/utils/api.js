import axios from 'axios';

// Use different URLs for different services
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8888';
const NEUROS_BASE = import.meta.env.VITE_NEUROS_URL || 'http://localhost:8000';

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
      // First try WebSocket if in development
      if (window.location.protocol === 'http:') {
        console.log('Using WebSocket for development...');
      }
      
      // Fall back to REST API
      console.log('Sending via REST API to NEUROS...');
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
      // For mixed content errors, provide user guidance
      if (error.code === 'ERR_NETWORK') {
        throw new Error('Network error - Please allow mixed content in your browser settings (click lock icon → Site settings → Insecure content → Allow)');
      }
      throw error;
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
