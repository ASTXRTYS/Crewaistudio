import React, { useState, useEffect } from 'react';
import KnowledgeGraph from './KnowledgeGraph';
import './AgentCard.css';

export default function AgentCard({ agentId, onClose }) {
  const [agentData, setAgentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  useEffect(() => {
    fetchAgentData();
  }, [agentId]);
  
  const fetchAgentData = async () => {
    try {
      const response = await fetch(`http://localhost:8080/api/agent-cards/${agentId}`);
      const data = await response.json();
      setAgentData(data);
    } catch (error) {
      console.error('Error fetching agent data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="agent-card loading">
        <div className="thinking-indicator"></div>
        <span>Loading agent data...</span>
      </div>
    );
  }
  
  if (!agentData) {
    return (
      <div className="agent-card error">
        <div className="error-indicator">Failed to load agent data</div>
      </div>
    );
  }
  
  return (
    <div className="agent-card expanded">
      <div className="agent-header">
        <div className="agent-profile">
          <div className="agent-avatar">
            <div className="neural-avatar">
              <span>{agentData.name.charAt(0)}</span>
            </div>
          </div>
          <div className="agent-info">
            <h2>{agentData.name}</h2>
            <span className="agent-specialization">{agentData.specialization}</span>
            <div className="agent-status">
              <span className={`status-indicator ${agentData.status}`}></span>
              <span>{agentData.status}</span>
            </div>
          </div>
        </div>
        {onClose && (
          <button className="close-button" onClick={onClose}>×</button>
        )}
      </div>
      
      <div className="agent-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'knowledge' ? 'active' : ''}`}
          onClick={() => setActiveTab('knowledge')}
        >
          Knowledge Graph
        </button>
        <button 
          className={`tab ${activeTab === 'hypotheses' ? 'active' : ''}`}
          onClick={() => setActiveTab('hypotheses')}
        >
          Hypotheses
        </button>
        <button 
          className={`tab ${activeTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setActiveTab('metrics')}
        >
          Metrics
        </button>
      </div>
      
      <div className="agent-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="metric-grid">
              <div className="metric-card">
                <div className="metric-value">{agentData.knowledge_count}</div>
                <div className="metric-label">Knowledge Items</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{agentData.active_hypotheses}</div>
                <div className="metric-label">Active Hypotheses</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">{agentData.accuracy}%</div>
                <div className="metric-label">Accuracy</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {agentData.performance_metrics.response_time_ms}ms
                </div>
                <div className="metric-label">Response Time</div>
              </div>
            </div>
            
            {agentData.last_breakthrough && (
              <div className="breakthrough-section">
                <h3>Last Breakthrough</h3>
                <div className="breakthrough-time">
                  {new Date(agentData.last_breakthrough).toLocaleString()}
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'knowledge' && (
          <div className="knowledge-section">
            <div className="knowledge-graph-wrapper">
              <KnowledgeGraph agentId={agentId} compact={true} />
            </div>
          </div>
        )}
        
        {activeTab === 'hypotheses' && (
          <div className="hypotheses-section">
            <div className="hypotheses-list">
              {/* Placeholder for hypotheses */}
              <div className="hypothesis-item">
                <h4>HRV Pattern Recognition</h4>
                <div className="hypothesis-progress">
                  <div className="hypothesis-progress-bar" style={{ width: '72%' }}></div>
                </div>
                <span className="hypothesis-confidence">72% Confidence</span>
              </div>
              <div className="hypothesis-item">
                <h4>Stress Response Optimization</h4>
                <div className="hypothesis-progress">
                  <div className="hypothesis-progress-bar" style={{ width: '45%' }}></div>
                </div>
                <span className="hypothesis-confidence">45% Confidence</span>
              </div>
              <div className="hypothesis-item">
                <h4>Recovery Protocol Enhancement</h4>
                <div className="hypothesis-progress">
                  <div className="hypothesis-progress-bar" style={{ width: '89%' }}></div>
                </div>
                <span className="hypothesis-confidence">89% Confidence</span>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'metrics' && (
          <div className="metrics-section">
            <div className="performance-chart">
              {/* Placeholder for performance charts */}
              <h3>Performance Metrics</h3>
              <div className="metric-item">
                <span>Decisions per Minute</span>
                <span className="metric-value-small">
                  {agentData.performance_metrics.decisions_per_minute}
                </span>
              </div>
              <div className="metric-item">
                <span>Knowledge Growth Rate</span>
                <span className="metric-value-small">
                  {agentData.performance_metrics.knowledge_growth_rate}x
                </span>
              </div>
            </div>
            
            {/* Domain-specific metrics for neuroscientist */}
            {agentData.specialization === 'CNS Optimization' && (
              <div className="domain-metrics">
                <h3>CNS Optimization Metrics</h3>
                <div className="metric-item">
                  <span>HRV Analysis Accuracy</span>
                  <span className="metric-value-small">96.3%</span>
                </div>
                <div className="metric-item">
                  <span>Neural Fatigue Detection</span>
                  <span className="metric-value-small">94.7%</span>
                </div>
                <div className="metric-item">
                  <span>Recovery Protocol Success</span>
                  <span className="metric-value-small">91.2%</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 