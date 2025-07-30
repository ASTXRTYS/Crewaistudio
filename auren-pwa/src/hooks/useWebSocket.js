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