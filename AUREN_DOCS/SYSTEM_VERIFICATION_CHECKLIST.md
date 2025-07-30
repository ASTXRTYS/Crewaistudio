# AUREN SYSTEM VERIFICATION CHECKLIST

Run this checklist after any deployment or significant configuration change to ensure system integrity.

## Backend Verification
- [ ] All Docker containers running and `Up`: `docker ps`
- [ ] NEUROS health check passes: `curl http://localhost:8000/health`
- [ ] Biometric service responds: `curl http://localhost:8888/health`
- [ ] PostgreSQL is accessible: `docker exec -it auren-postgres psql -U auren_user -c '\l'`
- [ ] Redis is operational: `docker exec -it auren-redis redis-cli ping` (should return PONG)
- [ ] Kafka is running and stable: `docker logs auren-kafka --tail 10`
- [ ] No critical disk space issues: `df -h` (ensure usage is < 90%)

## Frontend Verification
- [ ] PWA loads without an authentication wall at `https://auren-omacln1ad-jason-madrugas-projects.vercel.app/`
- [ ] No mixed content errors are visible in the browser's developer console.
- [ ] A test message can be successfully sent to NEUROS.
- [ ] A coherent response is received from the AI.
- [ ] The PWA displays correctly on both mobile and desktop viewports.

## Integration Verification
- [ ] The Vercel proxy for NEUROS is working: `curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health`
- [ ] The Vercel proxy for the Biometric service is working: `curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/biometric/health`
- [ ] CORS headers are present in responses when testing from a browser.
- [ ] No 404, 502, or other server errors in the browser's network tab.

## Monitoring Verification
- [ ] Prometheus is successfully scraping all targets: `http://144.126.215.218:9090/targets`
- [ ] Grafana dashboards are loading and displaying data: `http://144.126.215.218:3000`
- [ ] The master monitoring script runs without errors: `/root/monitor-auren.sh`

## Documentation Verification
- [ ] The change has been logged in `AUREN_DOCS/CHANGELOG.md`.
- [ ] All relevant SOPs have been updated to reflect the new configuration.
- [ ] The `SOP-003-AUREN-MASTER-TECHNICAL-SPECIFICATION.md` is accurate.
- [ ] The `SOP-001-AUREN-MASTER-OPERATIONS-GUIDE.md` is accurate.

**If any item on this checklist fails, consult the relevant SOP or runbook for resolution. Do not consider the deployment successful until all checks pass.** 