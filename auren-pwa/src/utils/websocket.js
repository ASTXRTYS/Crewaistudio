// WebSocket utility for AUREN PWA
// Handle mixed content limitations for WebSocket connections

// Detect if we're in production (Vercel) or development
const isProduction = window.location.hostname !== 'localhost';

// Use direct connection for now (will need HTTPS upgrade later)
const WS_URL = isProduction 
  ? 'ws://144.126.215.218:8888'  // Direct connection (will need HTTPS upgrade)
  : 'ws://localhost:8888';

// For production, show a message about WebSocket limitations
if (isProduction && window.location.protocol === 'https:') {
  console.warn('WebSocket connection may be blocked due to mixed content. Real-time features limited.');
}

export class AurenWebSocket {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    if (isProduction && window.location.protocol === 'https:') {
      console.warn('WebSocket connections from HTTPS to HTTP are blocked by browsers.');
      console.warn('Real-time features will use polling instead.');
      return false;
    }

    try {
      this.socket = new WebSocket(WS_URL);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.connected = true;
        this.reconnectAttempts = 0;
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.connected = false;
        this.handleReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return true;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      return false;
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, 1000 * this.reconnectAttempts);
    }
  }

  send(data) {
    if (this.connected && this.socket) {
      this.socket.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  close() {
    if (this.socket) {
      this.socket.close();
    }
  }
}

export const websocketUtils = {
  isWebSocketSupported: () => {
    if (isProduction && window.location.protocol === 'https:') {
      return false;
    }
    return 'WebSocket' in window;
  },
  
  getConnectionInfo: () => ({
    url: WS_URL,
    isProduction,
    protocol: window.location.protocol,
    supported: websocketUtils.isWebSocketSupported()
  })
}; 