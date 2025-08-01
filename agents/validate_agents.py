#!/usr/bin/env python3
"""
AUREN Agent Configuration Validation
Integrates with SOP-006 testing framework

Usage:
    python validate_agents.py              # Validate all
    python validate_agents.py --roster     # Validate roster only
    python validate_agents.py --modules    # Validate modules only
    pytest -v validate_agents.py           # Run via pytest
"""

import os
import sys
import json
import yaml
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse

# Try to import validation libraries
try:
    import yamllint.config
    import yamllint.linter
    YAMLLINT_AVAILABLE = True
except ImportError:
    YAMLLINT_AVAILABLE = False
    print("⚠️ yamllint not installed. Install with: pip install yamllint")

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("⚠️ jsonschema not installed. Install with: pip install jsonschema")

class AgentConfigValidator:
    """Comprehensive validation for AUREN agent configurations"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.path.dirname(__file__))
        self.errors = []
        self.warnings = []
        
        # Load schemas
        self.roster_schema = self._load_schema("schemas/roster-schema.json")
        self.module_schema = self._load_schema("schemas/agent-module-schema.json")
        
        # Configure yamllint
        self.yamllint_config = self._get_yamllint_config()
    
    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load JSON schema for validation"""
        full_path = self.base_path / schema_path
        if not full_path.exists():
            self.warnings.append(f"Schema not found: {schema_path}")
            return {}
        
        try:
            with open(full_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.errors.append(f"Failed to load schema {schema_path}: {e}")
            return {}
    
    def _get_yamllint_config(self) -> Any:
        """Configure yamllint rules"""
        if not YAMLLINT_AVAILABLE:
            return None
            
        config_content = """
rules:
  line-length:
    max: 120
  indentation:
    spaces: 2
  trailing-spaces: enable
  empty-lines:
    max: 2
    max-start: 1
    max-end: 1
  document-start:
    present: true
  comments:
    min-spaces-from-content: 1
"""
        return yamllint.config.YamlLintConfig(config_content)
    
    def validate_yaml_syntax(self, file_path: Path) -> List[str]:
        """Validate YAML syntax using yamllint"""
        if not YAMLLINT_AVAILABLE:
            return ["yamllint not available"]
        
        errors = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            problems = yamllint.linter.run(content, self.yamllint_config, file_path)
            for problem in problems:
                if problem.level == 'error':
                    errors.append(f"Line {problem.line}: {problem.message}")
                
        except Exception as e:
            errors.append(f"YAML syntax error: {e}")
        
        return errors
    
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any], file_path: str) -> List[str]:
        """Validate data against JSON schema"""
        if not JSONSCHEMA_AVAILABLE or not schema:
            return []
        
        errors = []
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error in {file_path}: {e.message}")
        except Exception as e:
            errors.append(f"Validation error in {file_path}: {e}")
        
        return errors
    
    def validate_roster(self) -> Tuple[bool, List[str]]:
        """Validate the main roster.yaml file"""
        roster_path = self.base_path / "roster.yaml"
        errors = []
        
        print(f"🔍 Validating roster: {roster_path}")
        
        if not roster_path.exists():
            return False, ["roster.yaml not found"]
        
        # YAML syntax validation
        yaml_errors = self.validate_yaml_syntax(roster_path)
        errors.extend(yaml_errors)
        
        # Load and validate structure
        try:
            with open(roster_path, 'r') as f:
                roster_data = yaml.safe_load(f)
                
            # JSON schema validation
            schema_errors = self.validate_json_schema(roster_data, self.roster_schema, "roster.yaml")
            errors.extend(schema_errors)
            
            # Business logic validation
            business_errors = self._validate_roster_business_logic(roster_data)
            errors.extend(business_errors)
            
        except Exception as e:
            errors.append(f"Failed to load roster.yaml: {e}")
        
        success = len(errors) == 0
        if success:
            print("✅ Roster validation passed")
        else:
            print(f"❌ Roster validation failed ({len(errors)} errors)")
            
        return success, errors
    
    def _validate_roster_business_logic(self, roster_data: Dict[str, Any]) -> List[str]:
        """Validate business rules for roster"""
        errors = []
        
        agents = roster_data.get("agents", {})
        
        # Check that we have exactly 9 agents
        if len(agents) != 9:
            errors.append(f"Expected 9 agents, found {len(agents)}")
        
        # Check that NEUROS is enabled (our operational agent)
        neuros = agents.get("NEUROS", {})
        if not neuros.get("enabled", False):
            errors.append("NEUROS must be enabled (operational requirement)")
        
        # Check status values are consistent
        for agent_name, agent_config in agents.items():
            status = agent_config.get("status")
            enabled = agent_config.get("enabled", False)
            
            if enabled and status == "todo":
                errors.append(f"{agent_name} is enabled but status is 'todo'")
            
            if not enabled and status not in ["todo"]:
                # Allow non-todo status for disabled agents (future planning)
                pass
        
        # Validate include paths exist
        for agent_name, agent_config in agents.items():
            includes = agent_config.get("include", [])
            if isinstance(includes, str):
                includes = [includes]
            
            for include_path in includes:
                full_path = self.base_path / include_path
                if not full_path.exists():
                    errors.append(f"{agent_name}: include path not found: {include_path}")
        
        return errors
    
    def validate_modules(self) -> Tuple[bool, List[str]]:
        """Validate all agent module files"""
        errors = []
        module_patterns = [
            "*_modules/*.yaml",
            "shared_modules/*.yaml"
        ]
        
        module_files = []
        for pattern in module_patterns:
            module_files.extend(glob.glob(str(self.base_path / pattern)))
        
        print(f"🔍 Validating {len(module_files)} module files")
        
        for module_file in module_files:
            module_path = Path(module_file)
            print(f"  📄 {module_path.name}")
            
            # YAML syntax validation
            yaml_errors = self.validate_yaml_syntax(module_path)
            errors.extend([f"{module_path.name}: {err}" for err in yaml_errors])
            
            # Schema validation (if module has content)
            try:
                with open(module_path, 'r') as f:
                    module_data = yaml.safe_load(f)
                
                if module_data:  # Skip empty/stub files
                    schema_errors = self.validate_json_schema(
                        module_data, self.module_schema, module_path.name
                    )
                    errors.extend(schema_errors)
            except Exception as e:
                errors.append(f"{module_path.name}: Failed to load: {e}")
        
        success = len(errors) == 0
        if success:
            print("✅ Module validation passed")
        else:
            print(f"❌ Module validation failed ({len(errors)} errors)")
            
        return success, errors
    
    def validate_topic_naming(self) -> Tuple[bool, List[str]]:
        """Validate Kafka topic naming conventions"""
        errors = []
        
        # Load integration protocols
        protocols_path = self.base_path / "shared_modules/integration_protocols.yaml"
        if not protocols_path.exists():
            return True, []  # Skip if file doesn't exist yet
        
        try:
            with open(protocols_path, 'r') as f:
                protocols = yaml.safe_load(f)
            
            example_topics = protocols.get("example_topics", {})
            pattern = r"^[a-z]+\.[a-z]+\.[a-z]+$"
            
            for category, topics in example_topics.items():
                if isinstance(topics, list):
                    for topic in topics:
                        import re
                        if not re.match(pattern, topic):
                            errors.append(f"Topic '{topic}' doesn't match pattern: {pattern}")
                            
        except Exception as e:
            errors.append(f"Failed to validate topic naming: {e}")
        
        return len(errors) == 0, errors
    
    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("🎯 AUREN Agent Configuration Validation")
        print("=" * 50)
        
        all_errors = []
        
        # Validate roster
        roster_success, roster_errors = self.validate_roster()
        all_errors.extend(roster_errors)
        
        # Validate modules
        modules_success, module_errors = self.validate_modules()
        all_errors.extend(module_errors)
        
        # Validate topic naming
        topics_success, topic_errors = self.validate_topic_naming()
        all_errors.extend(topic_errors)
        
        # Test loader functionality
        print("🔍 Testing configuration loader")
        try:
            sys.path.insert(0, str(self.base_path))
            from loader import test_loader
            loader_success = test_loader()
        except Exception as e:
            print(f"❌ Loader test failed: {e}")
            loader_success = False
            all_errors.append(f"Loader test failed: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        total_success = roster_success and modules_success and topics_success and loader_success
        
        if total_success:
            print("✅ ALL VALIDATIONS PASSED")
            print("🎯 Agent configuration is valid and ready for deployment")
        else:
            print(f"❌ VALIDATION FAILED ({len(all_errors)} total errors)")
            print("\nErrors:")
            for error in all_errors:
                print(f"  • {error}")
        
        return total_success

def main():
    """Main entry point for validation script"""
    parser = argparse.ArgumentParser(description="Validate AUREN agent configurations")
    parser.add_argument("--roster", action="store_true", help="Validate roster only")
    parser.add_argument("--modules", action="store_true", help="Validate modules only")
    parser.add_argument("--topics", action="store_true", help="Validate topic naming only")
    
    args = parser.parse_args()
    
    validator = AgentConfigValidator()
    
    if args.roster:
        success, errors = validator.validate_roster()
    elif args.modules:
        success, errors = validator.validate_modules()
    elif args.topics:
        success, errors = validator.validate_topic_naming()
    else:
        success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)

# Pytest integration
def test_roster_validation():
    """Pytest test for roster validation"""
    validator = AgentConfigValidator()
    success, errors = validator.validate_roster()
    assert success, f"Roster validation failed: {errors}"

def test_module_validation():
    """Pytest test for module validation"""
    validator = AgentConfigValidator()
    success, errors = validator.validate_modules()
    assert success, f"Module validation failed: {errors}"

def test_topic_naming_validation():
    """Pytest test for topic naming validation"""
    validator = AgentConfigValidator()
    success, errors = validator.validate_topic_naming()
    assert success, f"Topic naming validation failed: {errors}"

def test_loader_functionality():
    """Pytest test for loader functionality"""
    validator = AgentConfigValidator()
    try:
        from loader import test_loader
        assert test_loader(), "Loader test failed"
    except Exception as e:
        assert False, f"Loader import/test failed: {e}"

if __name__ == "__main__":
    main() 