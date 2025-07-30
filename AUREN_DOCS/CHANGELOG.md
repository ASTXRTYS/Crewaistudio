# AUREN SYSTEM CHANGELOG

## [1.0.0] - 2025-01-30 - PRODUCTION LAUNCH & CONFIGURATION LOCK

### Added
- ✅ **NEUROS AI Agent**: Deployed with LangGraph reasoning.
- ✅ **React PWA**: Live at `auren-omacln1ad-jason-madrugas-projects.vercel.app`.
- ✅ **Vercel Proxy**: Permanent solution for HTTPS/HTTP communication.
- ✅ **Docker Microservices**: Stable backend architecture on DigitalOcean.
- ✅ **Complete Data Pipeline**: PostgreSQL, Redis, and Kafka all integrated.
- ✅ **Full Observability**: Prometheus and Grafana for monitoring.
- ✅ **Comprehensive Documentation**: New SOPs, Architecture, and Runbooks created.

### Fixed
- ✅ **Mixed Content Blocking**: Resolved by implementing Vercel proxy rewrites.
- ✅ **CORS Errors**: Correctly configured on `neuros-advanced` for all Vercel domains.
- ✅ **Container Naming**: Standardized to `neuros-advanced` and `biometric-production`.
- ✅ **Vercel Authentication**: Disabled via `--public` flag, making the PWA accessible.

### Configuration
- **LOCKED**: The entire system configuration has been documented in `SOP-003` and is now considered the single source of truth. No changes are to be made without updating the documentation.

### Documentation
- **Consolidated**: All architectural, configuration, and procedural documents have been merged into two primary SOPs to create a single source of truth.
- **SOP-001**: Master Operations Guide (How to run the system).
- **SOP-003**: Master Technical Specification (What the system is).
- **New Additions**: `CHANGELOG.md` and `SYSTEM_VERIFICATION_CHECKLIST.md`.

### Known Issues
- WebSocket requires a direct `ws://` connection and may be blocked by browsers on HTTPS sites.
- The `biometric-production` service health check reports `healthy: false` due to unconfigured components, but the service itself is operational.

### Next Phase
- Address the known issues.
- Begin feature development on the stable, locked-in foundation.
- Implement a robust authentication layer (JWTs).
- Fully enable the biometric data pipeline. 