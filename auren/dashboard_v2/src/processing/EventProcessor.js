// Ring buffer for zero-allocation event processing
class RingBuffer {
  constructor(size = 10000) {
    this.buffer = new Float32Array(size);
    this.head = 0;
    this.tail = 0;
    this.size = size;
  }
  
  push(value) {
    this.buffer[this.head] = value;
    this.head = (this.head + 1) % this.size;
    if (this.head === this.tail) {
      this.tail = (this.tail + 1) % this.size;
    }
  }
  
  getRecent(count) {
    const result = [];
    let index = (this.head - count + this.size) % this.size;
    for (let i = 0; i < count; i++) {
      result.push(this.buffer[index]);
      index = (index + 1) % this.size;
    }
    return result;
  }
  
  clear() {
    this.head = 0;
    this.tail = 0;
  }
}

// Anomaly detector interface - simple statistics now, HTM later
class AnomalyDetector {
  constructor() {
    this.baseline = new RingBuffer(1000);
    this.threshold = 2.0; // Standard deviations
    this.adaptiveThreshold = 2.0;
    this.breakthroughThreshold = 5.0;
  }
  
  // This will be replaced with HTM network later
  detect(event) {
    const recentValues = this.baseline.getRecent(100);
    
    // Handle initial state
    if (recentValues.length < 10) {
      this.baseline.push(event.value || 0);
      return {
        isAnomaly: false,
        score: 0,
        timestamp: event.timestamp,
        type: 'normal'
      };
    }
    
    const mean = recentValues.reduce((a, b) => a + b, 0) / recentValues.length;
    const variance = recentValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / recentValues.length;
    const stdDev = Math.sqrt(variance);
    
    const value = event.value || 0;
    const anomalyScore = stdDev > 0 ? Math.abs(value - mean) / stdDev : 0;
    this.baseline.push(value);
    
    // Determine anomaly type
    let type = 'normal';
    if (anomalyScore > this.breakthroughThreshold) {
      type = 'breakthrough';
    } else if (anomalyScore > this.adaptiveThreshold) {
      type = 'anomaly';
    }
    
    return {
      isAnomaly: anomalyScore > this.threshold,
      score: anomalyScore,
      timestamp: event.timestamp,
      type,
      mean,
      stdDev,
      value
    };
  }
  
  updateThreshold(newThreshold) {
    this.adaptiveThreshold = newThreshold;
  }
}

// Event processor with WASM-ready structure
export class EventProcessor {
  constructor() {
    this.eventBuffer = new RingBuffer(10000);
    this.anomalyDetector = new AnomalyDetector();
    this.metrics = {
      eventsPerSecond: 0,
      avgProcessingTime: 0,
      anomaliesDetected: 0,
      breakthroughsDetected: 0,
      totalEvents: 0
    };
    this.lastEventTime = Date.now();
    this.eventCounts = [];
    this.processingTimes = new RingBuffer(1000);
  }
  
  processEvent(event) {
    const startTime = performance.now();
    
    // Process event
    this.eventBuffer.push(event.value || 0);
    const anomalyResult = this.anomalyDetector.detect(event);
    
    // Update metrics
    const processingTime = performance.now() - startTime;
    this.updateMetrics(processingTime, anomalyResult);
    
    return {
      event,
      anomaly: anomalyResult,
      processingTime,
      metrics: this.getMetrics()
    };
  }
  
  updateMetrics(processingTime, anomalyResult) {
    // Update processing time
    this.processingTimes.push(processingTime);
    
    // Update event counts
    const now = Date.now();
    this.eventCounts.push(now);
    // Remove events older than 1 second
    this.eventCounts = this.eventCounts.filter(t => now - t < 1000);
    
    // Update metrics
    this.metrics.totalEvents++;
    this.metrics.eventsPerSecond = this.eventCounts.length;
    
    const recentTimes = this.processingTimes.getRecent(100);
    this.metrics.avgProcessingTime = recentTimes.reduce((a, b) => a + b, 0) / recentTimes.length;
    
    if (anomalyResult.isAnomaly) {
      this.metrics.anomaliesDetected++;
      if (anomalyResult.type === 'breakthrough') {
        this.metrics.breakthroughsDetected++;
      }
    }
  }
  
  getMetrics() {
    return { ...this.metrics };
  }
  
  reset() {
    this.eventBuffer.clear();
    this.anomalyDetector.baseline.clear();
    this.processingTimes.clear();
    this.eventCounts = [];
    this.metrics = {
      eventsPerSecond: 0,
      avgProcessingTime: 0,
      anomaliesDetected: 0,
      breakthroughsDetected: 0,
      totalEvents: 0
    };
  }
}

// Export for future WASM integration
export { RingBuffer, AnomalyDetector }; 