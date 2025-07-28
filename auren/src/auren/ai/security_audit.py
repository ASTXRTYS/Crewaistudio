"""
Security Audit for Neuroscientist MVP - PHI Protection Validation.

This script audits the integration to ensure:
1. No PHI (Protected Health Information) in logs
2. Proper data sanitization in error messages
3. User context isolation
4. Secure communication between components
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Set
from pathlib import Path
import inspect
from unittest.mock import patch, MagicMock

from .gateway import AIGateway
from .langgraph_gateway_adapter import CrewAIGatewayAdapter, AgentContext
from .neuroscientist_integration_example import NeuroscientistSpecialist
from ..monitoring.otel_config import init_telemetry


class SecurityAuditResult:
    """Results from security audit."""
    
    def __init__(self):
        self.violations: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.passed_checks: List[str] = []
    
    def add_violation(self, check: str, details: str, severity: str = "HIGH"):
        """Add a security violation."""
        self.violations.append({
            "check": check,
            "details": details,
            "severity": severity
        })
    
    def add_warning(self, check: str, details: str):
        """Add a security warning."""
        self.warnings.append({
            "check": check,
            "details": details
        })
    
    def add_passed(self, check: str):
        """Mark a check as passed."""
        self.passed_checks.append(check)
    
    def is_compliant(self) -> bool:
        """Check if system is compliant (no high severity violations)."""
        high_severity = [v for v in self.violations if v["severity"] == "HIGH"]
        return len(high_severity) == 0
    
    def print_report(self):
        """Print the audit report."""
        print("\n" + "="*60)
        print("🔒 SECURITY AUDIT REPORT - Neuroscientist MVP")
        print("="*60)
        
        if self.is_compliant():
            print("\n✅ COMPLIANT - No critical security violations found")
        else:
            print("\n❌ NON-COMPLIANT - Critical violations detected")
        
        print(f"\n📊 Summary:")
        print(f"  Passed Checks: {len(self.passed_checks)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Violations: {len(self.violations)}")
        
        if self.violations:
            print("\n🚨 VIOLATIONS:")
            for v in self.violations:
                print(f"  [{v['severity']}] {v['check']}: {v['details']}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for w in self.warnings:
                print(f"  {w['check']}: {w['details']}")
        
        if self.passed_checks:
            print("\n✓ PASSED CHECKS:")
            for check in self.passed_checks:
                print(f"  ✓ {check}")


class PHIPatternDetector:
    """Detects potential PHI in strings."""
    
    # PHI patterns to detect
    PHI_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "dob": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        "medical_record": r"\b(MRN|Medical Record #?:?)\s*\d+\b",
        "patient_name": r"\b(Patient|Name):?\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b"
    }
    
    # Biometric data that should be handled carefully
    BIOMETRIC_KEYWORDS = {
        "hrv", "heart_rate", "blood_pressure", "glucose",
        "weight", "bmi", "body_fat", "vo2max"
    }
    
    @classmethod
    def contains_phi(cls, text: str) -> List[str]:
        """Check if text contains PHI patterns."""
        violations = []
        
        for phi_type, pattern in cls.PHI_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"Potential {phi_type} detected")
        
        return violations
    
    @classmethod
    def contains_biometric_data(cls, text: str) -> bool:
        """Check if text contains biometric keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.BIOMETRIC_KEYWORDS)


class NeuroscientistSecurityAuditor:
    """Security auditor for the Neuroscientist integration."""
    
    def __init__(self):
        self.result = SecurityAuditResult()
        self.logged_messages: List[str] = []
        self.error_messages: List[str] = []
    
    async def run_full_audit(self) -> SecurityAuditResult:
        """Run complete security audit."""
        print("🔍 Starting security audit...")
        
        # 1. Audit logging configuration
        await self._audit_logging_configuration()
        
        # 2. Audit error handling
        await self._audit_error_handling()
        
        # 3. Audit data isolation
        await self._audit_data_isolation()
        
        # 4. Audit communication security
        await self._audit_communication_security()
        
        # 5. Audit memory handling
        await self._audit_memory_handling()
        
        # 6. Audit token tracking
        await self._audit_token_tracking()
        
        return self.result
    
    async def _audit_logging_configuration(self):
        """Ensure logging doesn't expose PHI."""
        check_name = "Logging Configuration"
        
        # Create mock logger to capture logs
        mock_handler = MagicMock()
        mock_handler.emit = lambda record: self.logged_messages.append(
            record.getMessage()
        )
        
        # Test with biometric data
        test_data = {
            "hrv_current": 45,
            "user_email": "test@example.com",  # PHI
            "patient_name": "John Doe"  # PHI
        }
        
        # Create test components with mock logging
        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            logger_instance.handlers = [mock_handler]
            mock_logger.return_value = logger_instance
            
            # Test adapter logging
            adapter = CrewAIGatewayAdapter(
                ai_gateway=MagicMock(),
                default_model="gpt-3.5-turbo"
            )
            
            # Simulate logging scenarios
            logger_instance.info(f"Processing data: {test_data}")
            logger_instance.error(f"Failed with data: {test_data}")
        
        # Check for PHI in logs
        phi_found = False
        for msg in self.logged_messages:
            violations = PHIPatternDetector.contains_phi(msg)
            if violations:
                phi_found = True
                self.result.add_violation(
                    check_name,
                    f"PHI detected in logs: {violations}",
                    "HIGH"
                )
                break
        
        if not phi_found:
            self.result.add_passed(check_name)
    
    async def _audit_error_handling(self):
        """Ensure error messages don't expose PHI."""
        check_name = "Error Message Sanitization"
        
        # Test error scenarios
        test_contexts = [
            {
                "user_id": "user123",
                "biometric_data": {
                    "hrv_current": 45,
                    "ssn": "123-45-6789"  # Should never appear in errors
                }
            }
        ]
        
        # Mock gateway that throws errors
        mock_gateway = MagicMock()
        mock_gateway.complete.side_effect = Exception("Gateway error")
        
        adapter = CrewAIGatewayAdapter(ai_gateway=mock_gateway)
        
        for context_data in test_contexts:
            context = AgentContext(
                agent_name="Neuroscientist",
                user_id=context_data["user_id"],
                task_id="test_task",
                conversation_id="test_conv",
                memory_context=[],
                biometric_data=context_data["biometric_data"]
            )
            
            try:
                await adapter.execute_for_agent("Test prompt", context)
            except Exception as e:
                error_msg = str(e)
                self.error_messages.append(error_msg)
                
                # Check for PHI in error
                violations = PHIPatternDetector.contains_phi(error_msg)
                if violations:
                    self.result.add_violation(
                        check_name,
                        f"PHI in error message: {violations}",
                        "HIGH"
                    )
                elif PHIPatternDetector.contains_biometric_data(error_msg):
                    self.result.add_warning(
                        check_name,
                        "Biometric data mentioned in error message"
                    )
        
        if not any(v["check"] == check_name for v in self.result.violations):
            self.result.add_passed(check_name)
    
    async def _audit_data_isolation(self):
        """Ensure user data is properly isolated."""
        check_name = "User Data Isolation"
        
        # Create multiple user contexts
        user1_context = AgentContext(
            agent_name="Neuroscientist",
            user_id="user1",
            task_id="task1",
            conversation_id="conv1",
            memory_context=["User1 HRV baseline: 50ms"],
            biometric_data={"hrv_current": 50}
        )
        
        user2_context = AgentContext(
            agent_name="Neuroscientist",
            user_id="user2",
            task_id="task2",
            conversation_id="conv2",
            memory_context=["User2 HRV baseline: 40ms"],
            biometric_data={"hrv_current": 40}
        )
        
        # Test that contexts don't leak
        adapter = CrewAIGatewayAdapter(ai_gateway=MagicMock())
        
        # Build prompts for both users
        prompt1 = await adapter._build_contextual_prompt(
            "Analyze HRV", user1_context, MagicMock()
        )
        prompt2 = await adapter._build_contextual_prompt(
            "Analyze HRV", user2_context, MagicMock()
        )
        
        # Check for cross-contamination
        if "User2" in prompt1 or "40ms" in prompt1:
            self.result.add_violation(
                check_name,
                "User2 data found in User1 context",
                "HIGH"
            )
        elif "User1" in prompt2 or "50ms" in prompt2:
            self.result.add_violation(
                check_name,
                "User1 data found in User2 context",
                "HIGH"
            )
        else:
            self.result.add_passed(check_name)
    
    async def _audit_communication_security(self):
        """Ensure secure communication between components."""
        check_name = "Component Communication Security"
        
        # Check that gateway requests include proper authentication
        mock_gateway = MagicMock()
        adapter = CrewAIGatewayAdapter(ai_gateway=mock_gateway)
        
        context = AgentContext(
            agent_name="Neuroscientist",
            user_id="test_user",
            task_id="test_task",
            conversation_id="test_conv",
            memory_context=[],
            biometric_data={"hrv_current": 45}
        )
        
        # Intercept gateway calls
        calls = []
        async def mock_complete(request):
            calls.append(request)
            response = MagicMock()
            response.content = "Test response"
            response.prompt_tokens = 10
            response.completion_tokens = 10
            response.total_tokens = 20
            response.cost = 0.001
            return response
        
        mock_gateway.complete = mock_complete
        
        await adapter.execute_for_agent("Test", context)
        
        # Verify request structure
        if calls:
            request = calls[0]
            
            # Check for user identification
            if hasattr(request, 'user_id') and request.user_id:
                self.result.add_passed(check_name + " - User ID present")
            else:
                self.result.add_warning(
                    check_name,
                    "User ID not properly passed in request"
                )
            
            # Check for metadata
            if hasattr(request, 'metadata') and request.metadata:
                if 'agent' in request.metadata:
                    self.result.add_passed(check_name + " - Agent metadata")
                else:
                    self.result.add_warning(
                        check_name,
                        "Agent identification missing in metadata"
                    )
    
    async def _audit_memory_handling(self):
        """Ensure memory system handles PHI securely."""
        check_name = "Memory System Security"
        
        # Test memory storage
        memory_path = Path("/tmp/test_security_audit")
        memory_path.mkdir(exist_ok=True)
        
        try:
            # Create specialist with PHI in memory
            adapter = CrewAIGatewayAdapter(ai_gateway=MagicMock())
            specialist = NeuroscientistSpecialist(
                memory_path=memory_path,
                gateway_adapter=adapter
            )
            
            # Add hypothesis with potential PHI
            specialist.hypothesis_tracker.add_hypothesis(
                "User John Doe (SSN: 123-45-6789) responds to...",
                initial_confidence=0.5
            )
            
            # Save memory
            specialist._save_memory()
            
            # Check saved file
            memory_file = memory_path / "specialist_memory.json"
            if memory_file.exists():
                content = memory_file.read_text()
                violations = PHIPatternDetector.contains_phi(content)
                
                if violations:
                    self.result.add_violation(
                        check_name,
                        f"PHI found in memory storage: {violations}",
                        "HIGH"
                    )
                else:
                    self.result.add_passed(check_name)
            
        finally:
            # Cleanup
            import shutil
            if memory_path.exists():
                shutil.rmtree(memory_path)
    
    async def _audit_token_tracking(self):
        """Ensure token tracking doesn't expose PHI."""
        check_name = "Token Tracking Security"
        
        # Check that token tracking metadata is sanitized
        from ..monitoring.decorators import track_tokens
        
        # Mock function with PHI in parameters
        @track_tokens(model="gpt-3.5-turbo", agent_id="neuroscientist")
        async def test_function(prompt: str, user_ssn: str = "123-45-6789"):
            return "Response"
        
        # Intercept tracking calls
        tracked_data = []
        
        with patch('auren.monitoring.decorators.get_token_tracker') as mock_tracker:
            tracker_instance = MagicMock()
            
            async def mock_track_usage(**kwargs):
                tracked_data.append(kwargs)
            
            tracker_instance.track_usage = mock_track_usage
            mock_tracker.return_value = tracker_instance
            
            # Call function
            await test_function("Analyze HRV data")
        
        # Check tracked data for PHI
        if tracked_data:
            for data in tracked_data:
                metadata = data.get('metadata', {})
                metadata_str = str(metadata)
                
                violations = PHIPatternDetector.contains_phi(metadata_str)
                if violations:
                    self.result.add_violation(
                        check_name,
                        f"PHI in token tracking: {violations}",
                        "HIGH"
                    )
                    break
            else:
                self.result.add_passed(check_name)


async def run_security_audit():
    """Run the complete security audit."""
    auditor = NeuroscientistSecurityAuditor()
    result = await auditor.run_full_audit()
    result.print_report()
    
    return result.is_compliant()


if __name__ == "__main__":
    # Run security audit
    is_compliant = asyncio.run(run_security_audit())
    
    if is_compliant:
        print("\n✅ System is security compliant for PHI protection")
        exit(0)
    else:
        print("\n❌ Security violations detected - fix before deployment")
        exit(1) 