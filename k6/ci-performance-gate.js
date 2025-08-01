// AUREN CI Performance Gate Test
// Runs as part of CI/CD to ensure performance doesn't regress

import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 }
  ],
  thresholds: {
    // Strict thresholds for CI
    http_req_duration: [
      'p(95)<200', // 95th percentile must be under 200ms
      'p(99)<400', // 99th percentile must be under 400ms
      'max<1000'   // No request should take more than 1s
    ],
    http_req_failed: ['rate<0.001'], // 99.9% success rate
    checks: ['rate>0.99']            // 99% of checks must pass
  }
};

const BASE_URL = __ENV.BASE_URL || 'http://144.126.215.218:8000';

export default function() {
  // Test the main analyze endpoint
  const payload = JSON.stringify({
    message: 'CI performance test',
    user_id: `ci-user-${__VU}`,
    session_id: `ci-session-${__ITER}`
  });
  
  const params = {
    headers: { 'Content-Type': 'application/json' }
  };
  
  const res = http.post(`${BASE_URL}/api/agents/neuros/analyze`, payload, params);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
    'has valid response': (r) => {
      const body = JSON.parse(r.body);
      return body.response && body.kpi_emitted === true;
    }
  });
}

export function handleSummary(data) {
  // Return non-zero exit code if thresholds failed
  const failed = Object.values(data.metrics)
    .filter(metric => metric.thresholds)
    .some(metric => Object.values(metric.thresholds).includes(false));
  
  if (failed) {
    console.error('Performance gate failed! Thresholds not met.');
  }
  
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    './ci-performance-results.json': JSON.stringify(data)
  };
}

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';