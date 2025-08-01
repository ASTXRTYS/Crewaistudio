// AUREN Comprehensive Load Test Suite
// Tests: Smoke, Load, Stress, Spike, and Soak patterns

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const kpiEmissions = new Counter('kpi_emissions');
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency', true);

// Test configuration based on TEST_TYPE env var
const TEST_TYPE = __ENV.TEST_TYPE || 'smoke';

const scenarios = {
  smoke: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '1m', target: 5 },
      { duration: '2m', target: 5 },
      { duration: '1m', target: 0 }
    ],
    gracefulRampDown: '30s'
  },
  load: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '5m', target: 100 },
      { duration: '10m', target: 100 },
      { duration: '5m', target: 0 }
    ],
    gracefulRampDown: '30s'
  },
  stress: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 100 },
      { duration: '5m', target: 100 },
      { duration: '2m', target: 200 },
      { duration: '5m', target: 200 },
      { duration: '2m', target: 300 },
      { duration: '5m', target: 300 },
      { duration: '10m', target: 0 }
    ],
    gracefulRampDown: '30s'
  },
  spike: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '10s', target: 100 },
      { duration: '1m', target: 100 },
      { duration: '10s', target: 1000 },
      { duration: '3m', target: 1000 },
      { duration: '10s', target: 100 },
      { duration: '3m', target: 100 },
      { duration: '10s', target: 0 }
    ],
    gracefulRampDown: '30s'
  },
  soak: {
    executor: 'constant-vus',
    vus: 200,
    duration: '2h'
  }
};

export const options = {
  scenarios: {
    [TEST_TYPE]: scenarios[TEST_TYPE]
  },
  thresholds: {
    http_req_duration: ['p(95)<250'], // 95% of requests under 250ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
    errors: ['rate<0.01'],            // Custom error rate under 1%
    api_latency: ['p(99)<500']        // 99% under 500ms
  },
  noConnectionReuse: false,
  userAgent: 'AUREN-K6-LoadTest/1.0'
};

const BASE_URL = __ENV.BASE_URL || 'http://144.126.215.218:8000';

// Test data generators
function generateUserMessage() {
  const messages = [
    'Analyze my HRV data from this morning',
    'What is my current recovery score?',
    'How much sleep debt have I accumulated?',
    'Optimize my training load for today',
    'Review my stress levels from yesterday',
    'Provide CNS fatigue assessment',
    'Calculate my readiness score',
    'Analyze heart rate variability trends'
  ];
  return randomItem(messages);
}

function generateUserId() {
  return `k6-user-${__VU}-${Date.now()}`;
}

function generateSessionId() {
  return `k6-session-${__ITER}-${Date.now()}`;
}

// API wrapper functions
function testHealthEndpoint() {
  const res = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: 'health' }
  });
  
  check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check has kpi_enabled': (r) => {
      const body = JSON.parse(r.body);
      return body.kpi_enabled === true;
    },
    'health check response time < 50ms': (r) => r.timings.duration < 50
  }) || errorRate.add(1);
  
  return res;
}

function testAnalyzeEndpoint() {
  const payload = JSON.stringify({
    message: generateUserMessage(),
    user_id: generateUserId(),
    session_id: generateSessionId(),
    timestamp: new Date().toISOString()
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': `k6-${__VU}-${__ITER}`
    },
    tags: { endpoint: 'analyze' }
  };
  
  const res = http.post(`${BASE_URL}/api/agents/neuros/analyze`, payload, params);
  
  // Record custom metrics
  apiLatency.add(res.timings.duration);
  
  const success = check(res, {
    'analyze status 200': (r) => r.status === 200,
    'analyze has response': (r) => {
      const body = JSON.parse(r.body);
      return body.response && body.response.length > 0;
    },
    'analyze kpi emitted': (r) => {
      const body = JSON.parse(r.body);
      return body.kpi_emitted === true;
    },
    'analyze response time < 250ms': (r) => r.timings.duration < 250
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    kpiEmissions.add(1);
  }
  
  return res;
}

function testMetricsEndpoint() {
  const res = http.get(`${BASE_URL}/metrics`, {
    tags: { endpoint: 'metrics' }
  });
  
  check(res, {
    'metrics status 200': (r) => r.status === 200,
    'metrics has KPI data': (r) => {
      return r.body.includes('auren_hrv_rmssd_ms') &&
             r.body.includes('auren_sleep_debt_hours') &&
             r.body.includes('auren_recovery_score');
    }
  }) || errorRate.add(1);
  
  return res;
}

// Main test scenario
export default function() {
  group('AUREN API Tests', function() {
    // Test health endpoint (10% of requests)
    if (Math.random() < 0.1) {
      testHealthEndpoint();
    }
    
    // Main analyze endpoint (80% of requests)
    if (Math.random() < 0.8) {
      testAnalyzeEndpoint();
    }
    
    // Metrics endpoint (10% of requests)
    if (Math.random() < 0.1) {
      testMetricsEndpoint();
    }
  });
  
  // Simulate realistic user behavior
  sleep(randomItem([0.5, 1, 1.5, 2, 3]));
}

// Lifecycle hooks
export function setup() {
  console.log(`Starting ${TEST_TYPE} test against ${BASE_URL}`);
  
  // Verify service is up
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    throw new Error('Service is not healthy, aborting test');
  }
  
  return { testType: TEST_TYPE, startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`${data.testType} test completed in ${duration}s`);
}

// Handle test abort gracefully
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    [`./k6-results-${TEST_TYPE}-${Date.now()}.json`]: JSON.stringify(data)
  };
}

// Import required for summary
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';