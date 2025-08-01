// neuros_k6_smoke.js - KPI-enabled smoke test
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 20 },
    { duration: '30s', target: 0 }
  ],
  thresholds: {
    http_req_duration: ['p(95)<250']
  }
};

export default function() {
  // Test health endpoint
  let healthRes = http.get('http://144.126.215.218:8000/health');
  check(healthRes, { 
    'health status 200': (r) => r.status === 200,
    'kpi enabled': (r) => JSON.parse(r.body).kpi_enabled === true
  });
  
  // Test analyze endpoint with KPI emission
  let payload = JSON.stringify({
    message: 'K6 load test message',
    user_id: `k6-user-${__VU}`,
    session_id: `k6-session-${__ITER}`
  });
  
  let params = {
    headers: { 'Content-Type': 'application/json' }
  };
  
  let analyzeRes = http.post('http://144.126.215.218:8000/api/agents/neuros/analyze', payload, params);
  check(analyzeRes, {
    'analyze status 200': (r) => r.status === 200,
    'kpi emitted': (r) => JSON.parse(r.body).kpi_emitted === true
  });
  
  sleep(1);
}