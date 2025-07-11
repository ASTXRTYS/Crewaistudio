# SENIOR AGENT INSTRUCTIONS

## Purpose
This file serves as a centralized location for explicit instructions from the senior agent to Claude. Claude should refer to this file when instructed to check for guidance or when uncertain about implementation decisions.

## Current Instructions

### General Development Guidelines
- Always implement comprehensive error handling and logging
- Use type hints throughout the codebase
- Follow the established project structure and patterns
- Prioritize security and production readiness
- Maintain backward compatibility where possible

### Code Quality Standards
- All new code must include proper docstrings
- Unit tests required for new functionality
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Implement proper separation of concerns

### Security Requirements
- Use SHA-256 or stronger hashing algorithms (no MD5)
- Implement proper input validation
- Use secure file permissions (750/700)
- Sanitize all user inputs
- Log security-relevant events

### Testing Requirements
- Minimum 80% test coverage for new code
- Include both unit and integration tests
- Use proper mocking for external dependencies
- Test error conditions and edge cases
- Maintain test fixtures in conftest.py

### Documentation Standards
- Update README files when adding new features
- Document API endpoints and parameters
- Include usage examples in docstrings
- Maintain architectural decision records
- Update configuration documentation

## Specific Project Instructions

### AUREN 2.0 Framework
- Biometric data processing must be real-time capable
- All protocols (JOURNAL, MIRAGE, VISOR) must be thread-safe
- WhatsApp integration requires proper webhook handling
- RAG systems should be optimized for accuracy (95% target)
- Database operations must use ACID transactions

### Protocol Implementation
- Base protocol must support generic typing
- Error handling should be protocol-specific
- Logging must include correlation IDs
- Configuration should be YAML-based
- Tools must be factory-instantiated

### Agent Configuration
- Use YAML files for agent definitions
- Support dynamic tool loading
- Implement proper role-based access
- Include cost monitoring and limits
- Support multi-tenant operations

## Communication Protocol
- When uncertain, ask specific questions
- Provide implementation options when multiple approaches exist
- Always explain the reasoning behind architectural decisions
- Include performance and security considerations
- Document any deviations from established patterns

## Priority Levels
- **P0 (Critical)**: Security vulnerabilities, data corruption risks
- **P1 (High)**: Production blocking issues, performance degradation
- **P2 (Medium)**: Feature enhancements, code quality improvements
- **P3 (Low)**: Documentation updates, minor optimizations

## Contact Instructions
- Reference this file when instructed to "check senior agent instructions"
- Update this file when new guidance is provided
- Maintain version history of instruction changes
- Flag conflicts between instructions and implementation requirements

---
*Last Updated: [Current Date]*
*Version: 1.0* 