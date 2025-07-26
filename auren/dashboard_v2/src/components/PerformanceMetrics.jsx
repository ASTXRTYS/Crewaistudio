import { createSignal, onMount, onCleanup, createEffect } from 'solid-js';
import * as d3 from 'd3';
import { metricsState } from '../App';

export function PerformanceMetrics() {
  let chartRef;
  let sparklineRef;
  
  const [metrics, setMetrics] = createSignal({
    eventsPerSecond: 0,
    avgProcessingTime: 0,
    anomaliesDetected: 0,
    breakthroughsDetected: 0,
    totalEvents: 0
  });
  
  const [history, setHistory] = createSignal({
    eventRate: [],
    processingTime: []
  });
  
  // Subscribe to global metrics state
  createEffect(() => {
    const state = metricsState.get();
    if (state && typeof state === 'object') {
      setMetrics(state);
      
      // Update history for charts
      setHistory(prev => ({
        eventRate: [...prev.eventRate, {
          time: new Date(),
          value: state.eventsPerSecond || 0
        }].slice(-60), // Keep last 60 seconds
        processingTime: [...prev.processingTime, {
          time: new Date(),
          value: state.avgProcessingTime || 0
        }].slice(-60)
      }));
    }
  });
  
  onMount(() => {
    // Initialize event rate chart
    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const width = chartRef.offsetWidth - margin.left - margin.right;
    const height = 150 - margin.top - margin.bottom;
    
    const svg = d3.select(chartRef)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Scales
    const xScale = d3.scaleTime()
      .domain([new Date(Date.now() - 60000), new Date()])
      .range([0, width]);
    
    const yScale = d3.scaleLinear()
      .domain([0, 1000])
      .range([height, 0]);
    
    // Line generator
    const line = d3.line()
      .x(d => xScale(d.time))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX);
    
    // Add axes
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`);
    
    g.append('g')
      .attr('class', 'y-axis');
    
    // Add line path
    g.append('path')
      .attr('class', 'line event-rate-line')
      .style('fill', 'none')
      .style('stroke', '#4ade80')
      .style('stroke-width', 2);
    
    // Update function
    const updateChart = () => {
      const data = history().eventRate;
      
      // Update scales
      xScale.domain([
        new Date(Date.now() - 60000),
        new Date()
      ]);
      yScale.domain([0, Math.max(100, d3.max(data, d => d.value) * 1.2)]);
      
      // Update axes
      g.select('.x-axis')
        .call(d3.axisBottom(xScale)
          .ticks(5)
          .tickFormat(d3.timeFormat('%H:%M:%S')));
      
      g.select('.y-axis')
        .call(d3.axisLeft(yScale).ticks(5));
      
      // Update line
      g.select('.event-rate-line')
        .datum(data)
        .attr('d', line);
    };
    
    // Initialize sparkline for processing time
    const sparkWidth = sparklineRef.offsetWidth;
    const sparkHeight = 40;
    
    const sparkSvg = d3.select(sparklineRef)
      .append('svg')
      .attr('width', sparkWidth)
      .attr('height', sparkHeight);
    
    const sparkXScale = d3.scaleLinear()
      .domain([0, 60])
      .range([0, sparkWidth]);
    
    const sparkYScale = d3.scaleLinear()
      .domain([0, 50])
      .range([sparkHeight - 5, 5]);
    
    const sparkLine = d3.line()
      .x((d, i) => sparkXScale(i))
      .y(d => sparkYScale(d.value))
      .curve(d3.curveMonotoneX);
    
    sparkSvg.append('path')
      .attr('class', 'sparkline')
      .style('fill', 'none')
      .style('stroke', '#60a5fa')
      .style('stroke-width', 2);
    
    // Update sparkline
    const updateSparkline = () => {
      const data = history().processingTime;
      
      sparkYScale.domain([0, Math.max(10, d3.max(data, d => d.value) * 1.2)]);
      
      sparkSvg.select('.sparkline')
        .datum(data)
        .attr('d', sparkLine);
    };
    
    // Update interval
    const interval = setInterval(() => {
      updateChart();
      updateSparkline();
    }, 1000);
    
    onCleanup(() => {
      clearInterval(interval);
    });
  });
  
  // Format large numbers
  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toFixed(0);
  };
  
  return (
    <div class="performance-metrics-container">
      <div class="metrics-grid">
        <div class="metric-card primary">
          <div class="metric-header">
            <span class="metric-title">Events/Second</span>
            <span class="metric-trend">↑</span>
          </div>
          <div class="metric-value-large">
            {formatNumber(metrics().eventsPerSecond)}
          </div>
          <div class="metric-chart" ref={chartRef}></div>
        </div>
        
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Avg Processing Time</span>
          </div>
          <div class="metric-value-medium">
            {metrics().avgProcessingTime.toFixed(2)}ms
          </div>
          <div class="metric-sparkline" ref={sparklineRef}></div>
        </div>
        
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Total Events</span>
          </div>
          <div class="metric-value-medium">
            {formatNumber(metrics().totalEvents)}
          </div>
          <div class="metric-subtext">
            Since startup
          </div>
        </div>
        
        <div class="metric-card highlight">
          <div class="metric-header">
            <span class="metric-title">Anomalies Detected</span>
            <span class="metric-badge">AI</span>
          </div>
          <div class="metric-value-medium warning">
            {metrics().anomaliesDetected}
          </div>
          <div class="metric-subtext">
            {metrics().breakthroughsDetected} breakthroughs
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .performance-metrics-container {
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .metrics-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 16px;
          height: 100%;
        }
        
        .metric-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 12px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          transition: all 0.3s ease;
        }
        
        .metric-card:hover {
          background: rgba(30, 41, 59, 0.7);
          border-color: rgba(100, 116, 139, 0.5);
        }
        
        .metric-card.primary {
          grid-row: span 2;
        }
        
        .metric-card.highlight {
          border-color: rgba(251, 191, 36, 0.5);
          background: rgba(251, 191, 36, 0.1);
        }
        
        .metric-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .metric-title {
          font-size: 14px;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        
        .metric-trend {
          color: #4ade80;
          font-size: 18px;
        }
        
        .metric-badge {
          background: rgba(96, 165, 250, 0.2);
          color: #60a5fa;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
        }
        
        .metric-value-large {
          font-size: 48px;
          font-weight: 700;
          color: #e7e9ea;
          line-height: 1;
          margin-bottom: 16px;
        }
        
        .metric-value-medium {
          font-size: 32px;
          font-weight: 600;
          color: #e7e9ea;
          line-height: 1.2;
        }
        
        .metric-value-medium.warning {
          color: #fbbf24;
        }
        
        .metric-subtext {
          font-size: 13px;
          color: #64748b;
          margin-top: 8px;
        }
        
        .metric-chart {
          flex: 1;
          min-height: 150px;
          margin-top: 16px;
        }
        
        .metric-sparkline {
          height: 40px;
          margin-top: 12px;
        }
        
        /* D3 chart styles */
        :global(.x-axis text),
        :global(.y-axis text) {
          fill: #64748b;
          font-size: 11px;
        }
        
        :global(.x-axis line),
        :global(.y-axis line),
        :global(.x-axis path),
        :global(.y-axis path) {
          stroke: #334155;
        }
      `}</style>
    </div>
  );
} 