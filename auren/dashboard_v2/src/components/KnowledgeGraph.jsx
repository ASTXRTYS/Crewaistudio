import { createSignal, onMount, onCleanup } from 'solid-js';
import * as d3 from 'd3';

export function KnowledgeGraph() {
  let canvasRef;
  let simulation;
  let transform = d3.zoomIdentity;
  let ws = null;
  const [nodes, setNodes] = createSignal([]);
  const [links, setLinks] = createSignal([]);
  const [zoomLevel, setZoomLevel] = createSignal(1);
  const [loadingState, setLoadingState] = createSignal('initial');
  const [stats, setStats] = createSignal({ nodes: 0, links: 0, fps: 60 });
  const [agentId, setAgentId] = createSignal('neuroscientist'); // Default agent
  
  // Level of Detail thresholds
  const LOD_THRESHOLDS = {
    MINIMAL: 0.3,    // Just dots
    BASIC: 0.6,      // Dots + major connections  
    DETAILED: 1.2,   // + labels
    FULL: 2.0        // Everything
  };
  
  // Node size mapping
  const NODE_SIZES = {
    MIN: 2,
    MAX: 20,
    SCALE_FACTOR: 2
  };
  
  // Colors for different tiers and types
  const TIER_COLORS = {
    hot: 'hsla(0, 70%, 50%, 0.9)',    // Red - active memory
    warm: 'hsla(120, 70%, 50%, 0.7)', // Green - structured data
    cold: 'hsla(240, 70%, 50%, 0.5)'  // Blue - semantic knowledge
  };
  
  const TYPE_COLORS = {
    KNOWLEDGE: '#4ade80',
    EXPERIENCE: '#60a5fa', 
    INSIGHT: '#f59e0b',
    MEMORY: '#a78bfa',
    default: '#64748b'
  };
  
  onMount(() => {
    const canvas = canvasRef;
    const context = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    const height = canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    canvas.style.width = canvas.offsetWidth + 'px';
    canvas.style.height = canvas.offsetHeight + 'px';
    context.scale(window.devicePixelRatio, window.devicePixelRatio);
    
    // Initialize force simulation
    simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(d => d.id).distance(50).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-100).distanceMax(300))
      .force("center", d3.forceCenter(width / 2 / window.devicePixelRatio, height / 2 / window.devicePixelRatio))
      .force("collision", d3.forceCollide().radius(d => getNodeRadius(d, 1) + 2));
    
    // Setup WebSocket for real-time updates
    setupWebSocket();
    
    // FPS monitoring
    let lastTime = performance.now();
    let frameCount = 0;
    
    // Progressive loading function
    const loadNodesProgressive = async (depth) => {
      setLoadingState('loading');
      try {
        const data = await fetchKnowledgeGraphData(agentId(), depth);
        
        // Transform nodes for D3
        const transformedNodes = data.nodes.map(node => ({
          ...node,
          label: node.content.substring(0, 50) + (node.content.length > 50 ? '...' : ''),
          radius: NODE_SIZES.MIN + Math.sqrt(node.access_count || 1) * NODE_SIZES.SCALE_FACTOR,
          x: node.x || (Math.random() - 0.5) * 800 + 400,
          y: node.y || (Math.random() - 0.5) * 600 + 300
        }));
        
        setNodes(transformedNodes);
        setLinks(data.edges);
        
        // Update simulation
        simulation.nodes(transformedNodes);
        simulation.force("link").links(data.edges);
        simulation.alpha(1).restart();
        
        setLoadingState('loaded');
        setStats(prev => ({ 
          ...prev, 
          nodes: transformedNodes.length, 
          links: data.edges.length,
          ...data.stats 
        }));
      } catch (error) {
        console.error('Failed to load nodes:', error);
        setLoadingState('error');
      }
    };
    
    // Initial load - depth 1 (50 nodes from hot tier)
    loadNodesProgressive(1);
    
    // Render loop
    const render = () => {
      context.save();
      context.clearRect(0, 0, width / window.devicePixelRatio, height / window.devicePixelRatio);
      
      // Apply zoom transform
      context.translate(transform.x, transform.y);
      context.scale(transform.k, transform.k);
      
      const currentZoom = zoomLevel();
      const currentNodes = nodes();
      const currentLinks = links();
      
      // Draw based on zoom level
      if (currentZoom > LOD_THRESHOLDS.BASIC && currentLinks.length > 0) {
        // Draw links
        context.globalAlpha = Math.min(0.6, currentZoom / 2);
        currentLinks.forEach(link => {
          if (link.source && link.target) {
            const opacity = link.strength || 0.2;
            // Different line styles for different connection types
            if (link.type === 'tier_connection') {
              context.setLineDash([5, 5]);
              context.strokeStyle = `rgba(255, 255, 255, ${opacity * 0.5})`;
            } else {
              context.setLineDash([]);
              context.strokeStyle = `rgba(100, 148, 237, ${opacity})`;
            }
            context.lineWidth = Math.max(0.5, link.strength * 2);
            context.beginPath();
            context.moveTo(link.source.x, link.source.y);
            context.lineTo(link.target.x, link.target.y);
            context.stroke();
          }
        });
        context.setLineDash([]);
      }
      
      // Draw nodes
      context.globalAlpha = 1;
      currentNodes.forEach(node => {
        const radius = getNodeRadius(node, currentZoom);
        const color = getNodeColor(node);
        
        // Draw special shape for user context
        if (node.is_user_context) {
          // Draw diamond shape
          context.save();
          context.translate(node.x, node.y);
          context.rotate(Math.PI / 4);
          context.fillStyle = color;
          context.fillRect(-radius, -radius, radius * 2, radius * 2);
          context.restore();
          
          // Add pulsing effect for hot tier user context
          if (node.tier === 'hot' && node.glow) {
            const pulseRadius = radius + Math.sin(Date.now() * 0.003) * 5;
            context.beginPath();
            context.arc(node.x, node.y, pulseRadius, 0, 2 * Math.PI);
            context.strokeStyle = color;
            context.lineWidth = 2;
            context.globalAlpha = 0.5;
            context.stroke();
            context.globalAlpha = 1;
          }
        } else {
          // Regular circle for other nodes
          context.fillStyle = color;
          context.beginPath();
          context.arc(node.x, node.y, radius, 0, 2 * Math.PI);
          context.fill();
        }
        
        // Draw glow for frequently accessed nodes
        if (node.access_count > 10 || node.importance > 0.8) {
          context.shadowBlur = 20;
          context.shadowColor = color;
          context.fill();
          context.shadowBlur = 0;
        }
        
        // Draw labels if zoomed in enough
        if (currentZoom > LOD_THRESHOLDS.DETAILED && node.label) {
          context.fillStyle = '#e7e9ea';
          context.font = `${Math.max(12, 14 / currentZoom)}px sans-serif`;
          context.textAlign = 'center';
          context.fillText(node.label, node.x, node.y + radius + 15);
          
          // Show tier indicator
          context.font = `${Math.max(10, 12 / currentZoom)}px sans-serif`;
          context.fillStyle = TIER_COLORS[node.tier];
          context.fillText(`[${node.tier}]`, node.x, node.y + radius + 30);
        }
      });
      
      context.restore();
      
      // FPS calculation
      frameCount++;
      const currentTime = performance.now();
      if (currentTime - lastTime > 1000) {
        const fps = Math.round(frameCount * 1000 / (currentTime - lastTime));
        setStats(prev => ({ ...prev, fps }));
        frameCount = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(render);
    };
    
    simulation.on("tick", render);
    
    // Zoom handling with progressive loading
    const zoom = d3.zoom()
      .scaleExtent([0.1, 10])
      .on("zoom", (event) => {
        transform = event.transform;
        setZoomLevel(event.transform.k);
        
        // Progressive loading based on zoom
        const nodeCount = nodes().length;
        if (event.transform.k > 1.5 && nodeCount <= 50) {
          loadNodesProgressive(2); // Load warm tier
        } else if (event.transform.k > 3 && nodeCount <= 500) {
          loadNodesProgressive(3); // Load all tiers
        }
      });
    
    d3.select(canvas).call(zoom);
    
    // Handle resize
    const handleResize = () => {
      const newWidth = canvas.offsetWidth * window.devicePixelRatio;
      const newHeight = canvas.offsetHeight * window.devicePixelRatio;
      canvas.width = newWidth;
      canvas.height = newHeight;
      canvas.style.width = canvas.offsetWidth + 'px';
      canvas.style.height = canvas.offsetHeight + 'px';
      context.scale(window.devicePixelRatio, window.devicePixelRatio);
      simulation.force("center", d3.forceCenter(newWidth / 2 / window.devicePixelRatio, newHeight / 2 / window.devicePixelRatio));
      simulation.alpha(0.3).restart();
    };
    
    window.addEventListener('resize', handleResize);
    
    onCleanup(() => {
      window.removeEventListener('resize', handleResize);
      if (simulation) simulation.stop();
      if (ws) ws.close();
    });
  });
  
  // Helper functions
  function getNodeRadius(node, zoom) {
    const baseRadius = node.radius || NODE_SIZES.MIN;
    // Adjust size based on zoom to maintain visibility
    return Math.min(NODE_SIZES.MAX, Math.max(NODE_SIZES.MIN, baseRadius / Math.sqrt(zoom)));
  }
  
  function getNodeColor(node) {
    // Color based on tier takes precedence
    if (TIER_COLORS[node.tier]) {
      return TIER_COLORS[node.tier];
    }
    // Otherwise use type color
    return TYPE_COLORS[node.type] || TYPE_COLORS.default;
  }
  
  // Real API functions
  async function fetchKnowledgeGraphData(agentId, depth) {
    const response = await fetch(
      `/api/knowledge-graph/data?agent_id=${agentId}&depth=${depth}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch knowledge graph: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  // WebSocket setup for real-time updates
  function setupWebSocket() {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/dashboard/${agentId()}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Handle knowledge access events
      if (data.type === 'knowledge_access') {
        // Highlight the accessed node
        const accessedNodeId = data.memory_id;
        setNodes(prev => prev.map(node => {
          if (node.id === accessedNodeId) {
            return { ...node, access_count: (node.access_count || 0) + 1, glow: true };
          }
          return node;
        }));
        
        // Remove glow after 2 seconds
        setTimeout(() => {
          setNodes(prev => prev.map(node => {
            if (node.id === accessedNodeId) {
              return { ...node, glow: false };
            }
            return node;
          }));
        }, 2000);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      // Attempt to reconnect after 5 seconds
      setTimeout(setupWebSocket, 5000);
    };
  }
  
  return (
    <div class="knowledge-graph-container">
      <canvas ref={canvasRef} class="knowledge-canvas" />
      <div class="graph-overlay">
        <div class="graph-stats">
          <span>Nodes: {stats().nodes}</span>
          <span>Links: {stats().links}</span>
          <span>Zoom: {zoomLevel().toFixed(2)}x</span>
          <span>FPS: {stats().fps}</span>
          {stats().hot_tier_count !== undefined && (
            <>
              <span class="tier-stat hot">Hot: {stats().hot_tier_count}</span>
              <span class="tier-stat warm">Warm: {stats().warm_tier_count}</span>
              <span class="tier-stat cold">Cold: {stats().cold_tier_count}</span>
              <span class="user-context">Context: {stats().user_context_count}</span>
            </>
          )}
        </div>
        {loadingState() === 'loading' && (
          <div class="loading-indicator">Loading knowledge graph...</div>
        )}
        {loadingState() === 'error' && (
          <div class="error-indicator">Failed to load knowledge graph</div>
        )}
      </div>
      <div class="graph-controls">
        <button onClick={() => simulation && simulation.alpha(1).restart()}>
          Reset Layout
        </button>
        <select onChange={(e) => setAgentId(e.target.value)} value={agentId()}>
          <option value="neuroscientist">Neuroscientist</option>
          <option value="nutritionist">Nutritionist</option>
          <option value="trainer">Trainer</option>
        </select>
      </div>
    </div>
  );
} 