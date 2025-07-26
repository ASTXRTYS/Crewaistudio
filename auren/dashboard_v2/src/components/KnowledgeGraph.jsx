import { createSignal, onMount, onCleanup } from 'solid-js';
import * as d3 from 'd3';

export function KnowledgeGraph() {
  let canvasRef;
  let simulation;
  let transform = d3.zoomIdentity;
  const [nodes, setNodes] = createSignal([]);
  const [links, setLinks] = createSignal([]);
  const [zoomLevel, setZoomLevel] = createSignal(1);
  const [loadingState, setLoadingState] = createSignal('initial');
  const [stats, setStats] = createSignal({ nodes: 0, links: 0, fps: 60 });
  
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
  
  // Colors for different node types
  const NODE_COLORS = {
    knowledge: '#4ade80',
    hypothesis: '#60a5fa', 
    decision: '#f59e0b',
    memory: '#a78bfa',
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
    
    // FPS monitoring
    let lastTime = performance.now();
    let frameCount = 0;
    
    // Progressive loading function
    const loadNodesProgressive = async (count) => {
      setLoadingState('loading');
      try {
        // Simulate API call - replace with actual API
        const topNodes = await fetchTopNodes(count);
        const connections = await fetchConnections(topNodes.map(n => n.id));
        
        setNodes(topNodes);
        setLinks(connections);
        
        // Update simulation
        simulation.nodes(topNodes);
        simulation.force("link").links(connections);
        simulation.alpha(1).restart();
        
        setLoadingState('loaded');
        setStats(prev => ({ ...prev, nodes: topNodes.length, links: connections.length }));
      } catch (error) {
        console.error('Failed to load nodes:', error);
        setLoadingState('error');
      }
    };
    
    // Initial load - 50 nodes
    loadNodesProgressive(50);
    
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
            context.strokeStyle = `rgba(100, 148, 237, ${opacity})`;
            context.lineWidth = Math.max(0.5, link.strength * 2);
            context.beginPath();
            context.moveTo(link.source.x, link.source.y);
            context.lineTo(link.target.x, link.target.y);
            context.stroke();
          }
        });
      }
      
      // Draw nodes
      context.globalAlpha = 1;
      currentNodes.forEach(node => {
        const radius = getNodeRadius(node, currentZoom);
        const color = NODE_COLORS[node.type] || NODE_COLORS.default;
        
        // Draw node
        context.fillStyle = color;
        context.beginPath();
        context.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        context.fill();
        
        // Draw glow for active nodes
        if (node.active || node.usageCount > 50) {
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
        if (event.transform.k > 1.5 && nodeCount === 50) {
          loadNodesProgressive(500);
        } else if (event.transform.k > 3 && nodeCount === 500) {
          loadNodesProgressive(5000);
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
    });
  });
  
  // Helper functions
  function getNodeRadius(node, zoom) {
    const baseRadius = NODE_SIZES.MIN + Math.sqrt(node.connections || 1) * NODE_SIZES.SCALE_FACTOR;
    // Adjust size based on zoom to maintain visibility
    return Math.min(NODE_SIZES.MAX, Math.max(NODE_SIZES.MIN, baseRadius / Math.sqrt(zoom)));
  }
  
  // Mock data functions - replace with actual API calls
  async function fetchTopNodes(count) {
    await new Promise(resolve => setTimeout(resolve, 100)); // Simulate network delay
    return Array.from({ length: count }, (_, i) => ({
      id: `node-${i}`,
      label: `${['Knowledge', 'Hypothesis', 'Decision', 'Memory'][Math.floor(Math.random() * 4)]}-${i}`,
      type: ['knowledge', 'hypothesis', 'decision', 'memory'][Math.floor(Math.random() * 4)],
      usageCount: Math.floor(Math.random() * 100),
      connections: Math.floor(Math.random() * 20) + 1,
      active: Math.random() > 0.9,
      x: (Math.random() - 0.5) * 800 + 400,
      y: (Math.random() - 0.5) * 600 + 300
    }));
  }
  
  async function fetchConnections(nodeIds) {
    await new Promise(resolve => setTimeout(resolve, 50)); // Simulate network delay
    const connections = [];
    const nodeMap = new Map(nodeIds.map((id, index) => [id, index]));
    
    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < Math.min(i + 5, nodeIds.length); j++) {
        if (Math.random() > 0.7) {
          connections.push({
            source: nodeIds[i],
            target: nodeIds[j],
            strength: Math.random()
          });
        }
      }
    }
    return connections;
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
        </div>
        {loadingState() === 'loading' && (
          <div class="loading-indicator">Loading knowledge graph...</div>
        )}
      </div>
      <div class="graph-controls">
        <button onClick={() => simulation && simulation.alpha(1).restart()}>
          Reset Layout
        </button>
      </div>
    </div>
  );
} 