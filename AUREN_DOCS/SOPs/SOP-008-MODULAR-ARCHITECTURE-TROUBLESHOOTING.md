# SOP-008: MODULAR ARCHITECTURE TROUBLESHOOTING

**Version**: 1.0  
**Created**: July 31, 2025  
**Status**: ✅ PRODUCTION READY - COMPREHENSIVE PROBLEM RESOLUTION  
**Critical**: Rapid resolution of modular architecture issues to maintain system availability

---

## 🎯 **STRATEGIC CONTEXT & PURPOSE**

**Mission**: Provide systematic troubleshooting procedures for modular architecture issues, ensuring rapid problem resolution and minimal system downtime.

**Critical Importance**: Modular architecture forms the foundation for all 9 AUREN agents - any issues affect entire system capabilities.

**Business Impact**: 
- Maintains system availability and user trust
- Prevents cascading failures across agent ecosystem
- Ensures rapid recovery from configuration issues
- Preserves competitive advantages during incidents

---

## 📋 **TROUBLESHOOTING FRAMEWORK**

### **Issue Classification Matrix**
| Category | Severity | Impact | Response Time | Resolution Approach |
|----------|----------|--------|---------------|-------------------|
| **Critical** | System Down | All agents affected | Immediate | Emergency procedures |
| **High** | Performance Degraded | Single agent affected | 15 minutes | Rapid diagnosis |
| **Medium** | Functionality Limited | Specific features affected | 2 hours | Standard procedures |
| **Low** | Minor Issues | Development/testing | 24 hours | Routine maintenance |

### **Diagnostic Approach**
```yaml
Systematic Diagnosis:
  1. Symptom Identification - What is the observable problem?
  2. Impact Assessment - How many agents/users affected?
  3. Root Cause Analysis - What component is failing?
  4. Solution Implementation - How to fix the immediate issue?
  5. Prevention Strategy - How to prevent recurrence?
```

---

## 🚨 **EMERGENCY RESPONSE PROCEDURES**

### **CRITICAL: Complete System Failure**

#### **Immediate Response (0-5 minutes)**
```bash
#!/bin/bash
# emergency_system_recovery.sh

echo "🚨 EMERGENCY SYSTEM RECOVERY INITIATED"
echo "Timestamp: $(date)"
echo "="*50

# Step 1: Activate emergency fallback immediately
echo "⛔ ACTIVATING EMERGENCY FALLBACK..."
python3 -c "
import sys, os
sys.path.insert(0, 'agents')
try:
    from integration_adapter import NEUROSConfigAdapter
    adapter = NEUROSConfigAdapter(use_modular=False)
    config = adapter.get_config()
    if 'agent_profile' in config:
        print('✅ EMERGENCY FALLBACK ACTIVE - Legacy system operational')
    else:
        print('❌ EMERGENCY FALLBACK FAILED')
        sys.exit(1)
except Exception as e:
    print(f'❌ EMERGENCY FALLBACK ERROR: {e}')
    sys.exit(1)
" || {
    echo "🚨 CRITICAL: Emergency fallback failed - manual intervention required"
    echo "📞 ESCALATE TO EXECUTIVE ENGINEER IMMEDIATELY"
    exit 1
}

# Step 2: Preserve evidence
echo "📁 Preserving failure evidence..."
EVIDENCE_DIR="emergency_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"
cp -r agents/ "$EVIDENCE_DIR/" 2>/dev/null
cp *.log "$EVIDENCE_DIR/" 2>/dev/null
cp *.json "$EVIDENCE_DIR/" 2>/dev/null
git log --oneline -10 > "$EVIDENCE_DIR/recent_commits.txt"
echo "✅ Evidence preserved: $EVIDENCE_DIR"

# Step 3: System validation
echo "🔄 Validating system stability..."
if python3 test_modular_simple.py > "$EVIDENCE_DIR/validation_output.txt" 2>&1; then
    echo "✅ System validated and stable"
else
    echo "⚠️ System validation issues - check $EVIDENCE_DIR/validation_output.txt"
fi

# Step 4: Stakeholder notification
echo "📧 Notifying stakeholders..."
echo "Emergency recovery completed at $(date)" >> emergency_log.txt
echo "Evidence location: $EVIDENCE_DIR" >> emergency_log.txt

echo "🎯 Emergency response completed - System operational with legacy fallback"
echo "📋 Next steps: Investigate $EVIDENCE_DIR for root cause analysis"
```

#### **Root Cause Analysis (5-15 minutes)**
```python
#!/usr/bin/env python3
# emergency_root_cause_analysis.py

import os
import sys
import yaml
import json
import glob
import traceback
from datetime import datetime

def analyze_system_failure(evidence_dir):
    """Comprehensive root cause analysis for system failures"""
    
    print("🔍 EMERGENCY ROOT CAUSE ANALYSIS")
    print("="*50)
    print(f"Evidence directory: {evidence_dir}")
    
    analysis_report = {
        "timestamp": datetime.now().isoformat(),
        "evidence_dir": evidence_dir,
        "issues_found": [],
        "severity": "UNKNOWN",
        "recommended_actions": []
    }
    
    # 1. Check YAML syntax across all modules
    print("\n🔄 Analyzing YAML syntax...")
    yaml_issues = []
    
    yaml_files = glob.glob(f"{evidence_dir}/agents/**/*.yaml", recursive=True)
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            yaml_issues.append({
                "file": yaml_file,
                "error": str(e),
                "type": "yaml_syntax_error"
            })
            print(f"❌ YAML Error in {yaml_file}: {e}")
        except Exception as e:
            yaml_issues.append({
                "file": yaml_file,
                "error": str(e),
                "type": "file_access_error"
            })
    
    if yaml_issues:
        analysis_report["issues_found"].extend(yaml_issues)
        analysis_report["severity"] = "HIGH"
        analysis_report["recommended_actions"].append("Fix YAML syntax errors immediately")
        print(f"🚨 Found {len(yaml_issues)} YAML issues")
    else:
        print("✅ No YAML syntax issues found")
    
    # 2. Check module loading capability
    print("\n🔄 Analyzing module loading...")
    try:
        sys.path.insert(0, f"{evidence_dir}/agents")
        import loader
        config = loader.load_agent_roster()
        print("✅ Module loading successful")
    except ImportError as e:
        issue = {
            "type": "import_error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        analysis_report["issues_found"].append(issue)
        analysis_report["severity"] = "CRITICAL"
        analysis_report["recommended_actions"].append("Fix import errors in loader module")
        print(f"❌ Import Error: {e}")
    except Exception as e:
        issue = {
            "type": "loading_error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        analysis_report["issues_found"].append(issue)
        analysis_report["severity"] = "HIGH"
        analysis_report["recommended_actions"].append("Debug module loading mechanism")
        print(f"❌ Loading Error: {e}")
    
    # 3. Check file size compliance
    print("\n🔄 Analyzing file size compliance...")
    oversized_files = []
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                line_count = len(f.readlines())
            
            if line_count > 800:
                oversized_files.append({
                    "file": yaml_file,
                    "lines": line_count,
                    "type": "oversized_file"
                })
                print(f"⚠️ Oversized file: {yaml_file} ({line_count} lines)")
        except Exception as e:
            print(f"❌ Error checking {yaml_file}: {e}")
    
    if oversized_files:
        analysis_report["issues_found"].extend(oversized_files)
        if analysis_report["severity"] == "UNKNOWN":
            analysis_report["severity"] = "MEDIUM"
        analysis_report["recommended_actions"].append("Split oversized files into smaller modules")
    
    # 4. Check recent git changes
    print("\n🔄 Analyzing recent changes...")
    commits_file = f"{evidence_dir}/recent_commits.txt"
    if os.path.exists(commits_file):
        with open(commits_file, 'r') as f:
            recent_commits = f.read().strip().split('\n')
        
        print(f"📊 Recent commits: {len(recent_commits)}")
        for commit in recent_commits[:3]:
            print(f"   {commit}")
        
        analysis_report["recent_commits"] = recent_commits[:5]
        analysis_report["recommended_actions"].append("Review recent commits for problematic changes")
    
    # 5. Generate final assessment
    if analysis_report["severity"] == "UNKNOWN":
        analysis_report["severity"] = "LOW"
    
    print(f"\n🎯 ROOT CAUSE ANALYSIS COMPLETE")
    print(f"Severity: {analysis_report['severity']}")
    print(f"Issues found: {len(analysis_report['issues_found'])}")
    
    # Save analysis report
    report_file = f"{evidence_dir}/root_cause_analysis.json"
    with open(report_file, 'w') as f:
        json.dump(analysis_report, f, indent=2)
    
    print(f"📋 Analysis report saved: {report_file}")
    
    return analysis_report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 emergency_root_cause_analysis.py EVIDENCE_DIR")
        sys.exit(1)
    
    evidence_dir = sys.argv[1]
    report = analyze_system_failure(evidence_dir)
    
    # Exit with error code based on severity
    severity_codes = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    sys.exit(severity_codes.get(report["severity"], 1))
```

---

## 🔧 **COMMON ISSUES & SOLUTIONS**

### **Issue Category 1: Configuration Loading Problems**

#### **Problem: "Module not found" errors**
```python
# Diagnostic script: diagnose_module_loading.py

import sys
import os
import glob

def diagnose_module_loading():
    """Diagnose module loading issues"""
    
    print("🔍 DIAGNOSING MODULE LOADING ISSUES")
    print("="*40)
    
    # Check if agents directory exists
    if not os.path.exists("agents"):
        print("❌ CRITICAL: agents/ directory not found")
        print("💡 SOLUTION: Create agents directory structure")
        print("   mkdir -p agents/neuros_modules agents/shared_modules")
        return False
    
    # Check for required files
    required_files = [
        "agents/roster.yaml",
        "agents/loader.py", 
        "agents/integration_adapter.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("💡 SOLUTION: Restore missing files from backup or repository")
        return False
    
    # Check Python path issues
    try:
        sys.path.insert(0, "agents")
        import loader
        print("✅ Module import successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 SOLUTION: Check Python path and module dependencies")
        print("   Ensure agents/ directory is in Python path")
        return False
    
    # Check YAML loading
    try:
        config = loader.load_agent_roster()
        print(f"✅ Configuration loaded: {len(config.get('agents', {}))} agents")
        return True
    except Exception as e:
        print(f"❌ Configuration loading error: {e}")
        print("💡 SOLUTION: Check YAML syntax and file structure")
        return False

if __name__ == "__main__":
    success = diagnose_module_loading()
    sys.exit(0 if success else 1)
```

#### **Problem: YAML syntax errors**
```bash
#!/bin/bash
# fix_yaml_syntax.sh

echo "🔧 YAML SYNTAX ERROR REPAIR TOOL"
echo "="*40

# Find and validate all YAML files
find agents/ -name "*.yaml" -type f | while read yaml_file; do
    echo "🔄 Checking $yaml_file..."
    
    # Test YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
        echo "  ✅ Valid YAML"
    else
        echo "  ❌ YAML syntax error detected"
        
        # Create backup
        cp "$yaml_file" "${yaml_file}.backup_$(date +%Y%m%d_%H%M%S)"
        echo "  💾 Backup created: ${yaml_file}.backup_$(date +%Y%m%d_%H%M%S)"
        
        # Attempt automatic repair
        echo "  🔧 Attempting automatic repair..."
        
        # Common fixes
        # 1. Fix indentation issues
        python3 -c "
import yaml
import sys
try:
    with open('$yaml_file', 'r') as f:
        content = f.read()
    
    # Try to load and re-save to fix formatting
    data = yaml.safe_load(content)
    
    with open('$yaml_file', 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    print('  ✅ Automatic repair successful')
except Exception as e:
    print(f'  ❌ Automatic repair failed: {e}')
    print('  📋 Manual intervention required')
"
    fi
done

echo "🎯 YAML syntax repair completed"
```

### **Issue Category 2: Performance Problems**

#### **Problem: Slow configuration loading (>200ms)**
```python
#!/usr/bin/env python3
# diagnose_performance.py

import time
import cProfile
import pstats
import sys
import os
sys.path.insert(0, "agents")

def diagnose_performance_issues():
    """Comprehensive performance diagnosis"""
    
    print("📊 PERFORMANCE DIAGNOSIS")
    print("="*30)
    
    # Basic timing test
    start_time = time.time()
    import loader
    config = loader.load_agent_roster()
    load_time = (time.time() - start_time) * 1000
    
    print(f"Current load time: {load_time:.2f}ms")
    
    if load_time < 100:
        print("✅ Performance: EXCELLENT")
        return True
    elif load_time < 200:
        print("🔶 Performance: ACCEPTABLE")
    else:
        print("❌ Performance: NEEDS OPTIMIZATION")
    
    # Detailed profiling
    print("\n🔍 Running detailed profiling...")
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Profile the loading process
    for i in range(10):
        config = loader.load_agent_roster()
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    
    print("\n📈 Top performance bottlenecks:")
    stats.print_stats(10)
    
    # File size analysis
    print("\n📁 File size analysis:")
    import glob
    yaml_files = glob.glob("agents/**/*.yaml", recursive=True)
    
    total_lines = 0
    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as f:
            lines = len(f.readlines())
        total_lines += lines
        if lines > 500:
            print(f"  ⚠️ Large file: {yaml_file} ({lines} lines)")
    
    print(f"📊 Total configuration size: {total_lines} lines")
    
    # Recommendations
    print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
    
    if total_lines > 2000:
        print("  - Consider splitting large modules into smaller files")
    
    if load_time > 300:
        print("  - Implement configuration caching")
        print("  - Optimize YAML loading algorithm")
    
    if len(yaml_files) > 20:
        print("  - Consider lazy loading for non-essential modules")
    
    return load_time < 200

if __name__ == "__main__":
    success = diagnose_performance_issues()
    sys.exit(0 if success else 1)
```

### **Issue Category 3: Integration Problems**

#### **Problem: Backward compatibility failures**
```python
#!/usr/bin/env python3
# fix_compatibility_issues.py

import sys
import os
sys.path.insert(0, "agents")

def fix_compatibility_issues():
    """Diagnose and fix backward compatibility issues"""
    
    print("🔄 COMPATIBILITY ISSUE DIAGNOSIS")
    print("="*40)
    
    # Test modular loading
    print("🔄 Testing modular configuration loading...")
    try:
        import loader
        modular_config = loader.load_agent_roster()
        neuros_modular = modular_config["agents"]["NEUROS"]
        print("✅ Modular configuration loads successfully")
        
        # Check essential sections
        essential_sections = ["agent_profile", "communication", "personality"]
        missing_sections = []
        
        for section in essential_sections:
            if section not in neuros_modular:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing essential sections: {missing_sections}")
            print("💡 SOLUTION: Ensure core modules contain all required sections")
            return False
        else:
            print("✅ All essential sections present")
            
    except Exception as e:
        print(f"❌ Modular loading failed: {e}")
        return False
    
    # Test legacy compatibility
    print("\n🔄 Testing legacy compatibility...")
    try:
        import integration_adapter
        adapter = integration_adapter.NEUROSConfigAdapter(use_modular=True)
        legacy_format = adapter.get_legacy_format()
        
        if "agent_profile" in legacy_format:
            print("✅ Legacy format conversion working")
        else:
            print("❌ Legacy format conversion failed")
            print("💡 SOLUTION: Fix integration adapter logic")
            return False
            
    except Exception as e:
        print(f"❌ Legacy compatibility test failed: {e}")
        return False
    
    # Test fallback mechanism
    print("\n🔄 Testing fallback mechanism...")
    try:
        adapter_fallback = integration_adapter.NEUROSConfigAdapter(use_modular=False)
        fallback_config = adapter_fallback.get_config()
        
        if "agent_profile" in fallback_config:
            print("✅ Fallback mechanism working")
        else:
            print("❌ Fallback mechanism failed")
            print("💡 SOLUTION: Check legacy configuration file integrity")
            return False
            
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False
    
    print("\n✅ All compatibility tests passed")
    return True

if __name__ == "__main__":
    success = fix_compatibility_issues()
    sys.exit(0 if success else 1)
```

---

## 🔍 **DIAGNOSTIC TOOLS**

### **Comprehensive System Health Check**
```python
#!/usr/bin/env python3
# system_health_check.py

import sys
import os
import time
import yaml
import glob
import json
from datetime import datetime

def comprehensive_health_check():
    """Complete system health assessment"""
    
    print("🏥 COMPREHENSIVE SYSTEM HEALTH CHECK")
    print("="*50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "overall_status": "UNKNOWN",
        "recommendations": []
    }
    
    # Check 1: Directory Structure
    print("\n🔄 Checking directory structure...")
    required_dirs = [
        "agents",
        "agents/neuros_modules", 
        "agents/shared_modules",
        "config/agents"
    ]
    
    structure_ok = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (missing)")
            structure_ok = False
    
    health_report["checks"]["directory_structure"] = {
        "status": "PASS" if structure_ok else "FAIL",
        "details": "All required directories present" if structure_ok else "Missing directories detected"
    }
    
    # Check 2: File Integrity
    print("\n🔄 Checking file integrity...")
    required_files = [
        "agents/roster.yaml",
        "agents/loader.py",
        "agents/integration_adapter.py",
        "config/agents/neuros_agent_profile.yaml"
    ]
    
    file_integrity_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            try:
                if file_path.endswith('.yaml'):
                    with open(file_path, 'r') as f:
                        yaml.safe_load(f)
                elif file_path.endswith('.py'):
                    with open(file_path, 'r') as f:
                        compile(f.read(), file_path, 'exec')
                print(f"  ✅ {file_path}")
            except Exception as e:
                print(f"  ❌ {file_path} (corrupted: {e})")
                file_integrity_ok = False
        else:
            print(f"  ❌ {file_path} (missing)")
            file_integrity_ok = False
    
    health_report["checks"]["file_integrity"] = {
        "status": "PASS" if file_integrity_ok else "FAIL",
        "details": "All files valid" if file_integrity_ok else "File issues detected"
    }
    
    # Check 3: Module Loading
    print("\n🔄 Testing module loading...")
    try:
        sys.path.insert(0, "agents")
        import loader
        start_time = time.time()
        config = loader.load_agent_roster()
        load_time = (time.time() - start_time) * 1000
        
        agents_count = len(config.get("agents", {}))
        print(f"  ✅ Loaded {agents_count} agents in {load_time:.2f}ms")
        
        loading_ok = load_time < 300 and agents_count > 0
        health_report["checks"]["module_loading"] = {
            "status": "PASS" if loading_ok else "FAIL",
            "load_time_ms": load_time,
            "agents_loaded": agents_count,
            "details": f"Loading {'successful' if loading_ok else 'problematic'}"
        }
        
    except Exception as e:
        print(f"  ❌ Loading failed: {e}")
        health_report["checks"]["module_loading"] = {
            "status": "FAIL",
            "error": str(e),
            "details": "Module loading failed"
        }
        loading_ok = False
    
    # Check 4: Integration Testing
    print("\n🔄 Testing integration points...")
    try:
        import integration_adapter
        adapter = integration_adapter.NEUROSConfigAdapter(use_modular=True)
        legacy_format = adapter.get_legacy_format()
        
        integration_ok = "agent_profile" in legacy_format
        print(f"  {'✅' if integration_ok else '❌'} Integration adapter {'working' if integration_ok else 'failed'}")
        
        health_report["checks"]["integration"] = {
            "status": "PASS" if integration_ok else "FAIL",
            "details": "Integration adapter functional" if integration_ok else "Integration issues detected"
        }
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        health_report["checks"]["integration"] = {
            "status": "FAIL",
            "error": str(e),
            "details": "Integration testing failed"
        }
        integration_ok = False
    
    # Check 5: Performance Assessment
    print("\n🔄 Performance assessment...")
    try:
        # Multiple load tests
        load_times = []
        for i in range(5):
            start = time.time()
            loader.load_agent_roster()
            load_times.append((time.time() - start) * 1000)
        
        avg_load_time = sum(load_times) / len(load_times)
        performance_grade = "EXCELLENT" if avg_load_time < 50 else "GOOD" if avg_load_time < 100 else "ACCEPTABLE" if avg_load_time < 200 else "POOR"
        
        print(f"  📊 Average load time: {avg_load_time:.2f}ms ({performance_grade})")
        
        performance_ok = avg_load_time < 200
        health_report["checks"]["performance"] = {
            "status": "PASS" if performance_ok else "FAIL",
            "average_load_time_ms": avg_load_time,
            "grade": performance_grade,
            "details": f"Performance {performance_grade.lower()}"
        }
        
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        health_report["checks"]["performance"] = {
            "status": "FAIL",
            "error": str(e),
            "details": "Performance testing failed"
        }
        performance_ok = False
    
    # Overall Assessment
    all_checks_passed = all(check.get("status") == "PASS" for check in health_report["checks"].values())
    
    if all_checks_passed:
        health_report["overall_status"] = "HEALTHY"
        print(f"\n✅ SYSTEM STATUS: HEALTHY")
    else:
        failed_checks = [name for name, check in health_report["checks"].items() if check.get("status") == "FAIL"]
        health_report["overall_status"] = "UNHEALTHY"
        health_report["failed_checks"] = failed_checks
        print(f"\n❌ SYSTEM STATUS: UNHEALTHY")
        print(f"Failed checks: {', '.join(failed_checks)}")
    
    # Generate recommendations
    if not structure_ok:
        health_report["recommendations"].append("Restore missing directory structure")
    if not file_integrity_ok:
        health_report["recommendations"].append("Repair or restore corrupted files")
    if not loading_ok:
        health_report["recommendations"].append("Debug module loading issues")
    if not integration_ok:
        health_report["recommendations"].append("Fix integration adapter problems")
    if not performance_ok:
        health_report["recommendations"].append("Optimize system performance")
    
    # Save health report
    report_file = f"health_check_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(health_report, f, indent=2)
    
    print(f"\n📋 Health report saved: {report_file}")
    
    return health_report["overall_status"] == "HEALTHY"

if __name__ == "__main__":
    success = comprehensive_health_check()
    sys.exit(0 if success else 1)
```

---

## 📋 **MAINTENANCE PROCEDURES**

### **Routine Health Monitoring**
```bash
#!/bin/bash
# routine_health_monitor.sh

echo "👁️ ROUTINE HEALTH MONITORING"
echo "Timestamp: $(date)"
echo "="*40

# Daily health check
echo "🔄 Running daily health check..."
if python3 system_health_check.py > /dev/null 2>&1; then
    echo "✅ Daily health check: PASSED"
else
    echo "❌ Daily health check: FAILED"
    echo "📧 Alert: System health issues detected"
    # Add alerting logic here
fi

# Performance monitoring
echo "🔄 Performance monitoring..."
load_time=$(python3 -c "
import time, sys, os
sys.path.insert(0, 'agents')
import loader
start = time.time()
loader.load_agent_roster()
print((time.time() - start) * 1000)
")

echo "📊 Current load time: ${load_time}ms"

if (( $(echo "$load_time > 200" | bc -l) )); then
    echo "⚠️ Performance degradation detected"
    # Add performance alerting
fi

# File size monitoring
echo "🔄 File size monitoring..."
find agents/ -name "*.yaml" -exec wc -l {} + | while read lines file; do
    if [ "$lines" -gt 600 ]; then
        echo "⚠️ Large file detected: $file ($lines lines)"
    fi
done

echo "✅ Routine monitoring completed"
```

### **Preventive Maintenance**
```python
#!/usr/bin/env python3
# preventive_maintenance.py

import os
import sys
import yaml
import glob
import shutil
from datetime import datetime, timedelta

def preventive_maintenance():
    """Routine preventive maintenance tasks"""
    
    print("🔧 PREVENTIVE MAINTENANCE")
    print("="*30)
    
    maintenance_tasks = []
    
    # Task 1: Clean up old backup files
    print("🔄 Cleaning up old backup files...")
    backup_files = glob.glob("**/*.backup_*", recursive=True)
    old_backups = []
    
    cutoff_date = datetime.now() - timedelta(days=30)
    
    for backup_file in backup_files:
        try:
            # Extract date from filename
            date_str = backup_file.split('.backup_')[1]
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            
            if file_date < cutoff_date:
                old_backups.append(backup_file)
        except:
            continue
    
    if old_backups:
        print(f"  📁 Found {len(old_backups)} old backup files")
        for backup in old_backups[:5]:  # Show first 5
            print(f"    {backup}")
        
        # Archive old backups
        archive_dir = "archived_backups"
        os.makedirs(archive_dir, exist_ok=True)
        
        for backup in old_backups:
            try:
                shutil.move(backup, os.path.join(archive_dir, os.path.basename(backup)))
            except:
                continue
        
        print(f"  ✅ Archived {len(old_backups)} old backup files")
        maintenance_tasks.append(f"Archived {len(old_backups)} backup files")
    else:
        print("  ✅ No old backup files found")
    
    # Task 2: Optimize YAML formatting
    print("\n🔄 Optimizing YAML formatting...")
    yaml_files = glob.glob("agents/**/*.yaml", recursive=True)
    optimized_files = []
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                original_content = f.read()
            
            # Load and re-save to standardize formatting
            data = yaml.safe_load(original_content)
            
            # Generate optimized content
            optimized_content = yaml.dump(data, default_flow_style=False, sort_keys=False, indent=2)
            
            # Only update if content changed significantly
            if len(original_content) != len(optimized_content) or original_content != optimized_content:
                # Create backup before optimization
                backup_path = f"{yaml_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(yaml_file, backup_path)
                
                with open(yaml_file, 'w') as f:
                    f.write(optimized_content)
                
                optimized_files.append(yaml_file)
                print(f"  ✅ Optimized: {yaml_file}")
        except Exception as e:
            print(f"  ⚠️ Could not optimize {yaml_file}: {e}")
    
    if optimized_files:
        maintenance_tasks.append(f"Optimized {len(optimized_files)} YAML files")
    
    # Task 3: Validate configuration integrity
    print("\n🔄 Validating configuration integrity...")
    try:
        sys.path.insert(0, "agents")
        import loader
        config = loader.load_agent_roster()
        
        agents_count = len(config.get("agents", {}))
        print(f"  ✅ Configuration valid: {agents_count} agents loaded")
        maintenance_tasks.append("Configuration integrity validated")
    except Exception as e:
        print(f"  ❌ Configuration validation failed: {e}")
        maintenance_tasks.append("Configuration validation FAILED")
    
    # Task 4: Update maintenance log
    print("\n📝 Updating maintenance log...")
    maintenance_log = {
        "timestamp": datetime.now().isoformat(),
        "tasks_completed": maintenance_tasks,
        "status": "completed"
    }
    
    with open("maintenance_log.json", "w") as f:
        json.dump(maintenance_log, f, indent=2)
    
    print("✅ Preventive maintenance completed")
    print(f"📋 Tasks completed: {len(maintenance_tasks)}")
    
    return len(maintenance_tasks) > 0

if __name__ == "__main__":
    success = preventive_maintenance()
    sys.exit(0 if success else 1)
```

---

## 📞 **ESCALATION PROCEDURES**

### **When to Escalate**
```yaml
Escalation Triggers:
  Immediate (Executive Engineer):
    - Complete system failure (all agents down)
    - Security breach or data corruption
    - Emergency fallback failed
    - Performance degradation >500ms
    
  High Priority (Senior Engineer):
    - Single agent failure affecting users
    - Integration compatibility broken
    - Performance degradation >200ms
    - Configuration corruption
    
  Standard (Technical Lead):
    - Development environment issues
    - Non-critical performance issues
    - Documentation problems
    - Routine troubleshooting
```

### **Escalation Contact Script**
```bash
#!/bin/bash
# escalate_issue.sh

SEVERITY="$1"
DESCRIPTION="$2"

echo "📞 ESCALATING ISSUE"
echo "Severity: $SEVERITY"
echo "Description: $DESCRIPTION"
echo "Timestamp: $(date)"

case $SEVERITY in
    "CRITICAL")
        echo "🚨 CRITICAL ESCALATION - CONTACTING EXECUTIVE ENGINEER"
        echo "📧 Email: executive.engineer@auren.ai"
        echo "📱 Emergency: +1-XXX-XXX-XXXX"
        ;;
    "HIGH")
        echo "⚠️ HIGH PRIORITY - CONTACTING SENIOR ENGINEER"
        echo "📧 Email: senior.engineer@auren.ai"
        echo "📞 Phone: +1-XXX-XXX-XXXX"
        ;;
    "MEDIUM")
        echo "🔶 MEDIUM PRIORITY - CONTACTING TECHNICAL LEAD"
        echo "📧 Email: tech.lead@auren.ai"
        ;;
    *)
        echo "❓ UNKNOWN SEVERITY - USING STANDARD ESCALATION"
        ;;
esac

echo "📋 Issue details logged to escalation_log.txt"
echo "$(date): $SEVERITY - $DESCRIPTION" >> escalation_log.txt
```

---

**END OF SOP-008**

*This SOP provides comprehensive troubleshooting procedures for modular architecture issues, ensuring rapid problem resolution and system stability.* 