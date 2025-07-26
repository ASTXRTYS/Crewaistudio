import { createSignal, createEffect, For } from 'solid-js';
import { eventsState } from '../App';

export function EventStream() {
  const [events, setEvents] = createSignal([]);
  const [filter, setFilter] = createSignal('all');
  const [searchTerm, setSearchTerm] = createSignal('');
  
  // Subscribe to global events state
  createEffect(() => {
    const state = eventsState.get();
    if (Array.isArray(state)) {
      setEvents(state);
    }
  });
  
  // Generate mock events for development
  createEffect(() => {
    if (events().length === 0) {
      const mockEvents = [
        {
          id: 'evt-1',
          timestamp: Date.now() - 1000,
          agentId: 'neuroscientist',
          action: 'knowledge_access',
          details: 'Accessed HRV analysis protocols',
          value: 92,
          anomaly: { isAnomaly: false, score: 0.5, type: 'normal' },
          processingTime: 8.3
        },
        {
          id: 'evt-2',
          timestamp: Date.now() - 2500,
          agentId: 'neuroscientist',
          action: 'hypothesis_formed',
          details: 'Generated new recovery protocol hypothesis',
          value: 187,
          anomaly: { isAnomaly: true, score: 5.2, type: 'breakthrough' },
          processingTime: 12.1
        },
        {
          id: 'evt-3',
          timestamp: Date.now() - 4000,
          agentId: 'health_coordinator',
          action: 'decision_made',
          details: 'Recommended increased meditation frequency',
          value: 78,
          anomaly: { isAnomaly: false, score: 1.2, type: 'normal' },
          processingTime: 6.7
        }
      ];
      setEvents(mockEvents);
    }
  });
  
  // Filter events
  const filteredEvents = () => {
    let filtered = events();
    
    // Apply type filter
    if (filter() !== 'all') {
      filtered = filtered.filter(event => {
        if (filter() === 'anomalies') {
          return event.anomaly && event.anomaly.isAnomaly;
        }
        if (filter() === 'breakthroughs') {
          return event.anomaly && event.anomaly.type === 'breakthrough';
        }
        return event.action === filter();
      });
    }
    
    // Apply search filter
    if (searchTerm()) {
      const term = searchTerm().toLowerCase();
      filtered = filtered.filter(event => 
        event.details.toLowerCase().includes(term) ||
        event.agentId.toLowerCase().includes(term) ||
        event.action.toLowerCase().includes(term)
      );
    }
    
    return filtered;
  };
  
  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };
  
  // Get event type icon
  const getEventIcon = (action) => {
    switch (action) {
      case 'knowledge_access': return '📚';
      case 'hypothesis_formed': return '💡';
      case 'decision_made': return '🎯';
      case 'memory_stored': return '🧠';
      default: return '📊';
    }
  };
  
  // Get event severity class
  const getEventClass = (event) => {
    if (event.anomaly) {
      if (event.anomaly.type === 'breakthrough') return 'event-breakthrough';
      if (event.anomaly.isAnomaly) return 'event-anomaly';
    }
    return 'event-normal';
  };
  
  return (
    <div class="event-stream-container">
      <div class="event-controls">
        <div class="search-box">
          <input
            type="text"
            placeholder="Search events..."
            value={searchTerm()}
            onInput={(e) => setSearchTerm(e.target.value)}
            class="search-input"
          />
        </div>
        <div class="filter-buttons">
          <button
            class={`filter-btn ${filter() === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            class={`filter-btn ${filter() === 'anomalies' ? 'active' : ''}`}
            onClick={() => setFilter('anomalies')}
          >
            Anomalies
          </button>
          <button
            class={`filter-btn ${filter() === 'breakthroughs' ? 'active' : ''}`}
            onClick={() => setFilter('breakthroughs')}
          >
            Breakthroughs
          </button>
        </div>
      </div>
      
      <div class="event-list">
        <For each={filteredEvents()} fallback={<div class="no-events">No events to display</div>}>
          {(event) => (
            <div class={`event-item ${getEventClass(event)}`}>
              <div class="event-header">
                <span class="event-time">{formatTime(event.timestamp)}</span>
                <span class="event-agent">{event.agentId}</span>
                <span class="event-processing">{event.processingTime.toFixed(1)}ms</span>
              </div>
              <div class="event-body">
                <span class="event-icon">{getEventIcon(event.action)}</span>
                <div class="event-content">
                  <div class="event-action">{event.action.replace(/_/g, ' ')}</div>
                  <div class="event-details">{event.details}</div>
                </div>
                {event.anomaly && event.anomaly.isAnomaly && (
                  <div class="event-anomaly-badge">
                    {event.anomaly.score.toFixed(1)}σ
                  </div>
                )}
              </div>
            </div>
          )}
        </For>
      </div>
      
      <style jsx>{`
        .event-stream-container {
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .event-controls {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .search-box {
          flex: 1;
        }
        
        .search-input {
          width: 100%;
          padding: 8px 12px;
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #e7e9ea;
          font-size: 14px;
          transition: all 0.2s ease;
        }
        
        .search-input:focus {
          outline: none;
          border-color: #60a5fa;
          background: rgba(30, 41, 59, 0.8);
        }
        
        .search-input::placeholder {
          color: #64748b;
        }
        
        .filter-buttons {
          display: flex;
          gap: 8px;
        }
        
        .filter-btn {
          padding: 8px 16px;
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          color: #94a3b8;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        .filter-btn:hover {
          background: rgba(30, 41, 59, 0.7);
          border-color: rgba(100, 116, 139, 0.5);
          color: #e7e9ea;
        }
        
        .filter-btn.active {
          background: rgba(96, 165, 250, 0.2);
          border-color: #60a5fa;
          color: #60a5fa;
        }
        
        .event-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .event-item {
          background: rgba(30, 41, 59, 0.3);
          border: 1px solid rgba(100, 116, 139, 0.2);
          border-radius: 8px;
          padding: 12px;
          transition: all 0.2s ease;
        }
        
        .event-item:hover {
          background: rgba(30, 41, 59, 0.5);
          border-color: rgba(100, 116, 139, 0.4);
        }
        
        .event-normal {
          border-left: 3px solid #64748b;
        }
        
        .event-anomaly {
          border-left: 3px solid #fbbf24;
          background: rgba(251, 191, 36, 0.05);
        }
        
        .event-breakthrough {
          border-left: 3px solid #4ade80;
          background: rgba(74, 222, 128, 0.05);
          animation: glow 2s ease-in-out;
        }
        
        @keyframes glow {
          0%, 100% {
            box-shadow: none;
          }
          50% {
            box-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
          }
        }
        
        .event-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          font-size: 12px;
          color: #64748b;
        }
        
        .event-time {
          font-family: monospace;
        }
        
        .event-agent {
          color: #94a3b8;
          font-weight: 500;
        }
        
        .event-processing {
          color: #4ade80;
        }
        
        .event-body {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }
        
        .event-icon {
          font-size: 20px;
          line-height: 1;
        }
        
        .event-content {
          flex: 1;
        }
        
        .event-action {
          font-size: 14px;
          font-weight: 500;
          color: #e7e9ea;
          text-transform: capitalize;
          margin-bottom: 4px;
        }
        
        .event-details {
          font-size: 13px;
          color: #94a3b8;
          line-height: 1.4;
        }
        
        .event-anomaly-badge {
          background: rgba(251, 191, 36, 0.2);
          color: #fbbf24;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          white-space: nowrap;
        }
        
        .no-events {
          text-align: center;
          padding: 40px;
          color: #64748b;
        }
        
        /* Scrollbar styling */
        .event-list::-webkit-scrollbar {
          width: 6px;
        }
        
        .event-list::-webkit-scrollbar-track {
          background: rgba(30, 41, 59, 0.3);
          border-radius: 3px;
        }
        
        .event-list::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.5);
          border-radius: 3px;
        }
        
        .event-list::-webkit-scrollbar-thumb:hover {
          background: rgba(100, 116, 139, 0.7);
        }
      `}</style>
    </div>
  );
} 