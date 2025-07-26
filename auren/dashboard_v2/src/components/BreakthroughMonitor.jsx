import { createSignal, createEffect, For } from 'solid-js';
import { breakthroughsState } from '../App';

export function BreakthroughMonitor() {
  const [breakthroughs, setBreakthroughs] = createSignal([]);
  const [selectedBreakthrough, setSelectedBreakthrough] = createSignal(null);
  const [isReplaying, setIsReplaying] = createSignal(false);
  
  // Subscribe to global breakthroughs state
  createEffect(() => {
    const state = breakthroughsState.get();
    if (Array.isArray(state)) {
      setBreakthroughs(state);
    }
  });
  
  // Generate mock breakthroughs for development
  createEffect(() => {
    if (breakthroughs().length === 0) {
      const mockBreakthroughs = [
        {
          id: 'breakthrough-1',
          timestamp: Date.now() - 30000,
          agentId: 'neuroscientist',
          score: 5.2,
          type: 'breakthrough',
          description: '5.2σ deviation detected',
          data: {
            action: 'hypothesis_formed',
            details: 'Discovered correlation between HRV patterns and cognitive load',
            insight: 'When HRV coherence drops below 0.6 during high cognitive tasks, implementing 4-7-8 breathing pattern shows 47% improvement in recovery time'
          }
        },
        {
          id: 'breakthrough-2',
          timestamp: Date.now() - 120000,
          agentId: 'health_coordinator',
          score: 6.8,
          type: 'breakthrough',
          description: '6.8σ deviation detected',
          data: {
            action: 'pattern_discovered',
            details: 'Identified optimal recovery window timing',
            insight: 'Post-exercise recovery protocols are 3x more effective when initiated within 7-minute window after heart rate drops below 120bpm'
          }
        }
      ];
      setBreakthroughs(mockBreakthroughs);
    }
  });
  
  // Format time ago
  const formatTimeAgo = (timestamp) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };
  
  // Get score color
  const getScoreColor = (score) => {
    if (score >= 7) return '#ef4444'; // red - extreme
    if (score >= 5) return '#f59e0b'; // orange - significant
    return '#4ade80'; // green - notable
  };
  
  // Replay breakthrough
  const replayBreakthrough = (breakthrough) => {
    setSelectedBreakthrough(breakthrough);
    setIsReplaying(true);
    
    // Simulate replay animation
    setTimeout(() => {
      setIsReplaying(false);
    }, 3000);
  };
  
  return (
    <div class="breakthrough-monitor-container">
      <div class="monitor-header">
        <div class="status-indicator">
          <div class="pulse-dot"></div>
          <span>Monitoring Active</span>
        </div>
        <div class="stats">
          <span class="stat-item">
            <strong>{breakthroughs().length}</strong> detected
          </span>
        </div>
      </div>
      
      <div class="breakthrough-list">
        <For each={breakthroughs()} fallback={
          <div class="no-breakthroughs">
            <div class="empty-icon">🔍</div>
            <p>No breakthroughs detected yet</p>
            <p class="empty-subtext">The system will alert you when AI agents discover significant optimizations</p>
          </div>
        }>
          {(breakthrough) => (
            <div class="breakthrough-card">
              <div class="breakthrough-header">
                <div class="score-indicator" style={{
                  'background-color': getScoreColor(breakthrough.score)
                }}>
                  {breakthrough.score.toFixed(1)}σ
                </div>
                <div class="breakthrough-meta">
                  <span class="agent-name">{breakthrough.agentId}</span>
                  <span class="time-ago">{formatTimeAgo(breakthrough.timestamp)}</span>
                </div>
                <button
                  class="replay-btn"
                  onClick={() => replayBreakthrough(breakthrough)}
                  disabled={isReplaying() && selectedBreakthrough()?.id === breakthrough.id}
                >
                  {isReplaying() && selectedBreakthrough()?.id === breakthrough.id ? '⏸' : '▶'} Replay
                </button>
              </div>
              
              <div class="breakthrough-content">
                <div class="action-type">{breakthrough.data.action.replace(/_/g, ' ')}</div>
                <div class="details">{breakthrough.data.details}</div>
                {breakthrough.data.insight && (
                  <div class="insight">
                    <div class="insight-label">💡 Key Insight:</div>
                    <div class="insight-text">{breakthrough.data.insight}</div>
                  </div>
                )}
              </div>
              
              {selectedBreakthrough()?.id === breakthrough.id && isReplaying() && (
                <div class="replay-visualization">
                  <div class="replay-wave"></div>
                  <div class="replay-text">Replaying breakthrough moment...</div>
                </div>
              )}
            </div>
          )}
        </For>
      </div>
      
      <style jsx>{`
        .breakthrough-monitor-container {
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .monitor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 1px solid rgba(100, 116, 139, 0.2);
        }
        
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #4ade80;
          font-size: 14px;
        }
        
        .pulse-dot {
          width: 8px;
          height: 8px;
          background: #4ade80;
          border-radius: 50%;
          position: relative;
        }
        
        .pulse-dot::after {
          content: '';
          position: absolute;
          top: -4px;
          left: -4px;
          right: -4px;
          bottom: -4px;
          border: 2px solid #4ade80;
          border-radius: 50%;
          animation: pulse 2s infinite;
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
        
        .stats {
          display: flex;
          gap: 16px;
        }
        
        .stat-item {
          font-size: 14px;
          color: #94a3b8;
        }
        
        .stat-item strong {
          color: #e7e9ea;
          font-weight: 600;
        }
        
        .breakthrough-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .no-breakthroughs {
          text-align: center;
          padding: 60px 20px;
          color: #64748b;
        }
        
        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }
        
        .empty-subtext {
          font-size: 13px;
          margin-top: 8px;
          opacity: 0.8;
        }
        
        .breakthrough-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 12px;
          padding: 20px;
          transition: all 0.3s ease;
        }
        
        .breakthrough-card:hover {
          background: rgba(30, 41, 59, 0.7);
          border-color: rgba(100, 116, 139, 0.5);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .breakthrough-header {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 16px;
        }
        
        .score-indicator {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          font-weight: 700;
          color: #ffffff;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .breakthrough-meta {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        
        .agent-name {
          font-size: 16px;
          font-weight: 600;
          color: #e7e9ea;
          text-transform: capitalize;
        }
        
        .time-ago {
          font-size: 13px;
          color: #64748b;
        }
        
        .replay-btn {
          padding: 8px 16px;
          background: rgba(96, 165, 250, 0.2);
          border: 1px solid #60a5fa;
          border-radius: 8px;
          color: #60a5fa;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        
        .replay-btn:hover:not(:disabled) {
          background: rgba(96, 165, 250, 0.3);
          transform: translateY(-1px);
        }
        
        .replay-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .breakthrough-content {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .action-type {
          font-size: 14px;
          font-weight: 500;
          color: #94a3b8;
          text-transform: capitalize;
        }
        
        .details {
          font-size: 15px;
          color: #e7e9ea;
          line-height: 1.5;
        }
        
        .insight {
          background: rgba(74, 222, 128, 0.1);
          border: 1px solid rgba(74, 222, 128, 0.3);
          border-radius: 8px;
          padding: 16px;
          margin-top: 8px;
        }
        
        .insight-label {
          font-size: 13px;
          font-weight: 600;
          color: #4ade80;
          margin-bottom: 8px;
        }
        
        .insight-text {
          font-size: 14px;
          color: #e7e9ea;
          line-height: 1.6;
        }
        
        .replay-visualization {
          margin-top: 16px;
          padding: 20px;
          background: rgba(96, 165, 250, 0.05);
          border: 1px solid rgba(96, 165, 250, 0.2);
          border-radius: 8px;
          text-align: center;
        }
        
        .replay-wave {
          height: 40px;
          background: linear-gradient(90deg, 
            transparent 0%,
            rgba(96, 165, 250, 0.4) 25%,
            rgba(96, 165, 250, 0.8) 50%,
            rgba(96, 165, 250, 0.4) 75%,
            transparent 100%
          );
          animation: wave 2s linear infinite;
          margin-bottom: 12px;
        }
        
        @keyframes wave {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        
        .replay-text {
          font-size: 13px;
          color: #60a5fa;
        }
        
        /* Scrollbar styling */
        .breakthrough-list::-webkit-scrollbar {
          width: 6px;
        }
        
        .breakthrough-list::-webkit-scrollbar-track {
          background: rgba(30, 41, 59, 0.3);
          border-radius: 3px;
        }
        
        .breakthrough-list::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.5);
          border-radius: 3px;
        }
        
        .breakthrough-list::-webkit-scrollbar-thumb:hover {
          background: rgba(100, 116, 139, 0.7);
        }
      `}</style>
    </div>
  );
} 