import { createSignal, createEffect, For } from 'solid-js';
import { agentsState } from '../App';

export function AgentStatus() {
  const [agents, setAgents] = createSignal([]);
  
  // Subscribe to global agent state
  createEffect(() => {
    const state = agentsState.get();
    if (state && typeof state === 'object') {
      // Convert object to array for rendering
      const agentArray = Object.entries(state).map(([id, data]) => ({
        id,
        ...data
      }));
      setAgents(agentArray);
    }
  });
  
  // Mock data for development
  createEffect(() => {
    if (agents().length === 0) {
      // Set mock agents for UI development
      setAgents([
        {
          id: 'neuroscientist',
          name: 'Neuroscientist',
          status: 'thinking',
          lastActivity: Date.now() - 1000,
          performance: 92,
          tasksCompleted: 47,
          currentTask: 'Analyzing HRV patterns',
          responseTime: 8.3, // ms
          type: 'specialist'
        },
        {
          id: 'health_coordinator',
          name: 'Health Coordinator',
          status: 'idle',
          lastActivity: Date.now() - 5000,
          performance: 88,
          tasksCompleted: 125,
          currentTask: null,
          responseTime: 12.1,
          type: 'coordinator'
        }
      ]);
    }
  });
  
  // Get status color and animation
  const getStatusClass = (status) => {
    switch (status) {
      case 'thinking': return 'status-thinking pulse-fast';
      case 'processing': return 'status-processing pulse-medium';
      case 'idle': return 'status-idle pulse-slow';
      case 'error': return 'status-error';
      default: return 'status-unknown';
    }
  };
  
  // Format time ago
  const formatTimeAgo = (timestamp) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };
  
  // Get performance color
  const getPerformanceColor = (performance) => {
    if (performance >= 90) return '#4ade80'; // green
    if (performance >= 70) return '#fbbf24'; // yellow
    return '#ef4444'; // red
  };
  
  return (
    <div class="agent-status-container">
      <For each={agents()} fallback={<div class="no-agents">No agents connected</div>}>
        {(agent) => (
          <div class="agent-card">
            <div class="agent-header">
              <div class="agent-identity">
                <div class={`agent-status-indicator ${getStatusClass(agent.status)}`}></div>
                <h3 class="agent-name">{agent.name}</h3>
              </div>
              <span class="agent-type">{agent.type}</span>
            </div>
            
            <div class="agent-metrics">
              <div class="metric">
                <span class="metric-label">Performance</span>
                <div class="metric-value">
                  <div class="performance-bar">
                    <div 
                      class="performance-fill"
                      style={{
                        width: `${agent.performance}%`,
                        'background-color': getPerformanceColor(agent.performance)
                      }}
                    />
                  </div>
                  <span class="performance-text">{agent.performance}%</span>
                </div>
              </div>
              
              <div class="metric">
                <span class="metric-label">Response Time</span>
                <span class="metric-value highlight">{agent.responseTime.toFixed(1)}ms</span>
              </div>
              
              <div class="metric">
                <span class="metric-label">Tasks Completed</span>
                <span class="metric-value">{agent.tasksCompleted}</span>
              </div>
            </div>
            
            <div class="agent-activity">
              {agent.currentTask ? (
                <div class="current-task">
                  <span class="task-label">Current Task:</span>
                  <span class="task-description">{agent.currentTask}</span>
                </div>
              ) : (
                <div class="idle-status">Agent is idle</div>
              )}
              <span class="last-activity">
                Last active: {formatTimeAgo(agent.lastActivity)}
              </span>
            </div>
          </div>
        )}
      </For>
      
      <style jsx>{`
        .agent-status-container {
          display: grid;
          gap: 16px;
        }
        
        .agent-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 12px;
          padding: 20px;
          transition: all 0.3s ease;
        }
        
        .agent-card:hover {
          background: rgba(30, 41, 59, 0.7);
          border-color: rgba(100, 116, 139, 0.5);
          transform: translateY(-2px);
        }
        
        .agent-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .agent-identity {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .agent-status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          position: relative;
        }
        
        .status-thinking {
          background: #60a5fa;
        }
        
        .status-processing {
          background: #f59e0b;
        }
        
        .status-idle {
          background: #64748b;
        }
        
        .status-error {
          background: #ef4444;
        }
        
        .pulse-fast::after {
          content: '';
          position: absolute;
          top: -4px;
          left: -4px;
          right: -4px;
          bottom: -4px;
          border-radius: 50%;
          border: 2px solid currentColor;
          animation: pulse 1s infinite;
        }
        
        .pulse-medium::after {
          animation: pulse 2s infinite;
        }
        
        .pulse-slow::after {
          animation: pulse 3s infinite;
        }
        
        @keyframes pulse {
          0% {
            transform: scale(1);
            opacity: 1;
          }
          100% {
            transform: scale(1.5);
            opacity: 0;
          }
        }
        
        .agent-name {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #e7e9ea;
        }
        
        .agent-type {
          font-size: 12px;
          text-transform: uppercase;
          color: #64748b;
          background: rgba(100, 116, 139, 0.2);
          padding: 4px 8px;
          border-radius: 4px;
        }
        
        .agent-metrics {
          display: grid;
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .metric {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .metric-label {
          font-size: 14px;
          color: #94a3b8;
        }
        
        .metric-value {
          font-size: 16px;
          font-weight: 500;
          color: #e7e9ea;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .metric-value.highlight {
          color: #4ade80;
        }
        
        .performance-bar {
          width: 100px;
          height: 4px;
          background: rgba(100, 116, 139, 0.3);
          border-radius: 2px;
          overflow: hidden;
        }
        
        .performance-fill {
          height: 100%;
          transition: width 0.3s ease;
        }
        
        .performance-text {
          font-size: 14px;
        }
        
        .agent-activity {
          padding-top: 12px;
          border-top: 1px solid rgba(100, 116, 139, 0.2);
        }
        
        .current-task {
          margin-bottom: 8px;
        }
        
        .task-label {
          font-size: 14px;
          color: #94a3b8;
          margin-right: 8px;
        }
        
        .task-description {
          font-size: 14px;
          color: #e7e9ea;
        }
        
        .idle-status {
          font-size: 14px;
          color: #64748b;
          font-style: italic;
          margin-bottom: 8px;
        }
        
        .last-activity {
          font-size: 12px;
          color: #64748b;
        }
        
        .no-agents {
          text-align: center;
          padding: 40px;
          color: #64748b;
        }
      `}</style>
    </div>
  );
} 