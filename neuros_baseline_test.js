import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp up to 10 VUs
    { duration: '3m', target: 10 },  // Stay at 10 VUs
    { duration: '1m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    errors: ['rate<0.1'],             // Error rate under 10%
  },
};

export default function() {
  // Test NEUROS health endpoint
  let healthResponse = http.get('http://144.126.215.218:8001/health');
  
  check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  // Test NEUROS conversation endpoint
  let conversationPayload = JSON.stringify({
    message: "Hello, this is a load test message",
    user_id: "test_user_" + Math.random().toString(36).substr(2, 9),
    session_id: "test_session_" + Math.random().toString(36).substr(2, 9)
  });

  let conversationResponse = http.post(
    'http://144.126.215.218:8001/api/agents/neuros/analyze',
    conversationPayload,
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  check(conversationResponse, {
    'conversation status is 200': (r) => r.status === 200,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  }) || errorRate.add(1);

  sleep(1); // 1 second between iterations
}