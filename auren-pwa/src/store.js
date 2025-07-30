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