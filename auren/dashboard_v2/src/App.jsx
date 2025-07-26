import { createSignal, onMount, onCleanup, createEffect } from 'solid-js';
import { atom } from 'nanostores';
import { KnowledgeGraph } from './components/KnowledgeGraph';
import { AgentStatus } from './components/AgentStatus';
import { PerformanceMetrics } from './components/PerformanceMetrics';
import { EventStream } from './components/EventStream';
import { BreakthroughMonitor } from './components/BreakthroughMonitor';
import { EventProcessor } from './processing/EventProcessor';

// Global state atoms
export const agentsState = atom({});
export const metricsState = atom({});
export const eventsState = atom([]);
export const breakthroughsState = atom([]);

export default function App() {
  let ws;
  let reconnectTimeout;
  const eventProcessor = new EventProcessor();
  const [connectionStatus, setConnectionStatus] = createSignal('disconnected');
  const [wsUrl] = createSignal('ws://144.126.215.218:8001/ws');
  
  // Throttle function for 100ms updates
  const throttle = (func, delay) => {
    let timeoutId;
    let lastTime = 0;
    return (...args) => {
      const now = Date.now();
      clearTimeout(timeoutId);
      if (now - lastTime >= delay) {
        func(...args);
        lastTime = now;
      } else {
        timeoutId = setTimeout(() => {
          func(...args);
          lastTime = Date.now();
        }, delay - (now - lastTime));
      }
    };
  };
  
  // Update UI with throttling
  const updateUI = throttle((updates) => {
    if (updates.agents) agentsState.set(updates.agents);
    if (updates.metrics) metricsState.set(updates.metrics);
    if (updates.events) {
      const currentEvents = eventsState.get();
      eventsState.set([...updates.events, ...currentEvents].slice(0, 100));
    }
    if (updates.breakthrough) {
      const currentBreakthroughs = breakthroughsState.get();
      breakthroughsState.set([updates.breakthrough, ...currentBreakthroughs].slice(0, 50));
    }
  }, 100);
  
  // WebSocket connection management
  let reconnectDelay = 1000;
  const maxDelay = 30000;
  
  const connect = () => {
    try {
      ws = new WebSocket(wsUrl());
      
      ws.onopen = () => {
        console.log('✅ Connected to AUPEX consciousness stream');
        setConnectionStatus('connected');
        reconnectDelay = 1000; // Reset delay on successful connection
        
        // Send initial handshake
        ws.send(JSON.stringify({
          type: 'handshake',
          client: 'aupex-dashboard-v2',
          version: '2.0.0'
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Process different message types
          switch (data.type) {
            case 'agent_event':
              processAgentEvent(data);
              break;
            case 'system_metrics':
              processSystemMetrics(data);
              break;
            case 'knowledge_update':
              processKnowledgeUpdate(data);
              break;
            default:
              // Legacy format support
              if (data.agents || data.metrics || data.events) {
                processLegacyData(data);
              }
          }
        } catch (error) {
          console.error('Failed to process message:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnectionStatus('error');
      };
      
      ws.onclose = () => {
        setConnectionStatus('disconnected');
        console.log('🔄 WebSocket closed, reconnecting...');
        
        // Clear any existing timeout
        clearTimeout(reconnectTimeout);
        
        // Exponential backoff reconnection with jitter
        const jitter = Math.random() * 1000;
        reconnectTimeout = setTimeout(() => {
          reconnectDelay = Math.min(reconnectDelay * 2, maxDelay);
          connect();
        }, reconnectDelay + jitter);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  };
  
  // Process agent events through the pipeline
  const processAgentEvent = (data) => {
    const processed = eventProcessor.processEvent({
      timestamp: data.timestamp || Date.now(),
      value: data.value || Math.random() * 100,
      agentId: data.agentId,
      action: data.action,
      details: data.details
    });
    
    // Update UI
    updateUI({
      events: [{
        ...processed.event,
        anomaly: processed.anomaly,
        processingTime: processed.processingTime
      }],
      metrics: processed.metrics
    });
    
    // Check for breakthroughs
    if (processed.anomaly.type === 'breakthrough') {
      captureBreakthrough(processed);
    }
  };
  
  // Process system metrics
  const processSystemMetrics = (data) => {
    updateUI({ metrics: data.metrics });
  };
  
  // Process knowledge graph updates
  const processKnowledgeUpdate = (data) => {
    // Knowledge updates will be handled by the KnowledgeGraph component
    // through a separate WebSocket connection or polling
  };
  
  // Legacy data format support
  const processLegacyData = (data) => {
    // Process each event through our pipeline
    if (data.events && Array.isArray(data.events)) {
      data.events.forEach(event => {
        const processed = eventProcessor.processEvent(event);
        
        updateUI({
          events: [processed.event],
          metrics: processed.metrics
        });
        
        if (processed.anomaly.isAnomaly && processed.anomaly.score > 5) {
          captureBreakthrough(processed);
        }
      });
    }
    
    // Direct updates for agents and metrics
    if (data.agents) updateUI({ agents: data.agents });
    if (data.metrics) updateUI({ metrics: data.metrics });
  };
  
  // Capture breakthrough moments
  const captureBreakthrough = (event) => {
    const breakthrough = {
      id: `breakthrough-${Date.now()}`,
      timestamp: event.event.timestamp,
      agentId: event.event.agentId,
      score: event.anomaly.score,
      type: event.anomaly.type,
      description: `${event.anomaly.score.toFixed(1)}σ deviation detected`,
      data: event.event,
      replay: [] // Will store event sequence for replay
    };
    
    console.log('🎯 BREAKTHROUGH DETECTED!', breakthrough);
    updateUI({ breakthrough });
  };
  
  onMount(() => {
    connect();
  });
  
  onCleanup(() => {
    clearTimeout(reconnectTimeout);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });
  
  // Connection status styling
  const getStatusClass = () => {
    const status = connectionStatus();
    return `connection-status ${status}`;
  };
  
  return (
    <div class="aupex-dashboard">
      <header class="dashboard-header">
        <div class="header-content">
          <h1 class="dashboard-title">
            <span class="title-prefix">AUPEX</span>
            <span class="title-main">Consciousness Monitor</span>
          </h1>
          <div class="header-right">
            <div class={getStatusClass()}>
              <span class="status-indicator"></span>
              <span class="status-text">{connectionStatus()}</span>
            </div>
          </div>
        </div>
      </header>
      
      <main class="dashboard-grid">
        <section class="panel agent-status-panel">
          <div class="panel-header">
            <h2>Agent Status</h2>
            <span class="panel-badge">Live</span>
          </div>
          <div class="panel-content">
            <AgentStatus />
          </div>
        </section>
        
        <section class="panel knowledge-graph-panel">
          <div class="panel-header">
            <h2>Live Knowledge Graph</h2>
            <span class="panel-info">GPU Accelerated</span>
          </div>
          <div class="panel-content">
            <KnowledgeGraph />
          </div>
        </section>
        
        <section class="panel breakthrough-panel">
          <div class="panel-header">
            <h2>Breakthrough Detection</h2>
            <span class="panel-badge pulse">HTM Active</span>
          </div>
          <div class="panel-content">
            <BreakthroughMonitor />
          </div>
        </section>
        
        <section class="panel metrics-panel">
          <div class="panel-header">
            <h2>Performance Metrics</h2>
            <span class="panel-info">WASM Powered</span>
          </div>
          <div class="panel-content">
            <PerformanceMetrics />
          </div>
        </section>
        
        <section class="panel events-panel">
          <div class="panel-header">
            <h2>Event Stream</h2>
            <span class="panel-info">100ms Latency</span>
          </div>
          <div class="panel-content">
            <EventStream />
          </div>
        </section>
      </main>
      
      <footer class="dashboard-footer">
        <div class="footer-content">
          <span class="footer-text">AUPEX v2.0 - AI Consciousness Monitor</span>
          <span class="footer-stats">
            Processing: {metricsState.get().eventsPerSecond || 0} events/sec
          </span>
        </div>
      </footer>
    </div>
  );
} 