#!/usr/bin/env python3
"""
Comprehensive Module Fixes
Systematically fixes all identified issues across AUREN modules
"""

import os
import re
import json
import subprocess
from pathlib import Path

class ModuleFixer:
    def __init__(self):
        self.issues_fixed = []
        self.project_root = Path(__file__).parent
        
    def fix_websocket_path_issue(self):
        """Fix the SimpleWebSocketServer path argument issue"""
        print("🔧 Fixing WebSocket server path issue...")
        
        ws_file = self.project_root / "simple_websocket_server.py"
        if ws_file.exists():
            with open(ws_file, 'r') as f:
                content = f.read()
            
            # Fix the handle_client method signature
            content = content.replace(
                "async def handle_client(self, websocket, path):",
                "async def handle_client(self, websocket):"
            )
            
            with open(ws_file, 'w') as f:
                f.write(content)
            
            self.issues_fixed.append("Fixed WebSocket handle_client path argument issue")
    
    def fix_demo_neuroscientist_events(self):
        """Fix the demo_neuroscientist.py AURENStreamEvent issues"""
        print("🔧 Fixing demo_neuroscientist.py event issues...")
        
        demo_file = self.project_root / "auren" / "demo" / "demo_neuroscientist.py"
        if not demo_file.exists():
            return
            
        with open(demo_file, 'r') as f:
            lines = f.readlines()
        
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Fix AURENStreamEvent instantiation missing arguments
            if 'AURENStreamEvent(' in line and 'event_type=' in line:
                # Look for the closing parenthesis
                j = i
                while j < len(lines) and ')' not in lines[j]:
                    j += 1
                
                # Check if trace_id, target_agent, metadata are missing
                block = ''.join(lines[i:j+1])
                if 'trace_id=' not in block:
                    # Add missing arguments before the closing parenthesis
                    lines[j] = lines[j].replace(')', 
                        ',\n            trace_id=str(uuid.uuid4()),\n'
                        '            target_agent="neuroscientist",\n'
                        '            metadata={}\n        )')
                    self.issues_fixed.append(f"Added missing arguments to AURENStreamEvent at line {i+1}")
            
            fixed_lines.append(lines[i])
            i += 1
        
        with open(demo_file, 'w') as f:
            f.writelines(fixed_lines)
    
    def fix_import_paths(self):
        """Fix import path issues in test files"""
        print("🔧 Fixing import path issues...")
        
        # Update imports in test files
        test_files = list((self.project_root / "auren" / "tests").glob("*.py"))
        
        for test_file in test_files:
            with open(test_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix common import issues
            content = content.replace('from src.', 'from auren.src.')
            content = content.replace('from auren.src.auren.', 'from auren.')
            
            if content != original_content:
                with open(test_file, 'w') as f:
                    f.write(content)
                self.issues_fixed.append(f"Fixed imports in {test_file.name}")
    
    def check_and_install_dependencies(self):
        """Check and install missing dependencies"""
        print("🔧 Checking and installing missing dependencies...")
        
        missing_packages = []
        
        # Check for common missing packages
        packages_to_check = [
            'pydantic-settings',
            'aiohttp',
            'websockets',
            'redis',
            'asyncpg',
            'boto3',
            'pandas',
            'pyarrow',
            'psutil',
            'opentelemetry-api',
            'opentelemetry-sdk',
            'hvac'  # HashiCorp Vault
        ]
        
        for package in packages_to_check:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"📦 Installing missing packages: {', '.join(missing_packages)}")
            subprocess.run(['pip', 'install'] + missing_packages, check=True)
            self.issues_fixed.append(f"Installed missing packages: {', '.join(missing_packages)}")
    
    def fix_dashboard_api_path(self):
        """Fix dashboard API to serve the correct dashboard"""
        print("🔧 Fixing dashboard API path...")
        
        api_file = self.project_root / "auren" / "api" / "dashboard_api.py"
        if api_file.exists():
            with open(api_file, 'r') as f:
                content = f.read()
            
            # Fix the dashboard path
            if 'dashboard_path = "auren/dashboard/realtime_dashboard.html"' in content:
                content = content.replace(
                    'dashboard_path = "auren/dashboard/realtime_dashboard.html"',
                    '''# Try multiple dashboard locations
    dashboard_paths = [
        Path(__file__).parent.parent / "docs" / "context" / "auren-realtime-dashboard.html",
        Path(__file__).parent.parent / "dashboard" / "realtime_dashboard.html",
        "auren/docs/context/auren-realtime-dashboard.html",
        "auren/dashboard/realtime_dashboard.html"
    ]
    
    dashboard_path = None
    for path in dashboard_paths:
        if Path(path).exists() or os.path.exists(str(path)):
            dashboard_path = str(path)
            break'''
                )
                
                with open(api_file, 'w') as f:
                    f.write(content)
                
                self.issues_fixed.append("Fixed dashboard API to serve correct dashboard file")
    
    def update_requirements_files(self):
        """Update requirements files with all necessary dependencies"""
        print("🔧 Updating requirements files...")
        
        auren_req_file = self.project_root / "auren" / "requirements.txt"
        
        required_packages = [
            'fastapi>=0.100.0',
            'uvicorn[standard]>=0.23.0',
            'websockets>=12.0',
            'redis>=5.0.0',
            'aiohttp>=3.9.0',
            'boto3>=1.28.0',
            'pandas>=2.0.0',
            'pyarrow>=12.0.0',
            'psutil>=5.9.0',
            'pydantic>=2.0.0',
            'pydantic-settings>=2.0.0',
            'asyncpg>=0.28.0',
            'opentelemetry-api>=1.20.0',
            'opentelemetry-sdk>=1.20.0',
            'hvac>=1.1.0',
            'prometheus-client>=0.17.0'
        ]
        
        if auren_req_file.exists():
            with open(auren_req_file, 'r') as f:
                existing = f.read()
            
            for package in required_packages:
                pkg_name = package.split('>=')[0].split('[')[0]
                if pkg_name not in existing:
                    existing += f"\n{package}"
            
            with open(auren_req_file, 'w') as f:
                f.write(existing.strip() + "\n")
            
            self.issues_fixed.append("Updated auren/requirements.txt with missing dependencies")
    
    def fix_event_streaming_imports(self):
        """Fix event streaming import issues"""
        print("🔧 Fixing event streaming imports...")
        
        streaming_files = [
            self.project_root / "auren" / "realtime" / "enhanced_websocket_streamer.py",
            self.project_root / "auren" / "realtime" / "multi_protocol_streaming.py"
        ]
        
        for file_path in streaming_files:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Fix deprecated imports
                content = content.replace(
                    'from websockets.server import WebSocketServerProtocol',
                    'from websockets import WebSocketServerProtocol'
                )
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                self.issues_fixed.append(f"Fixed imports in {file_path.name}")
    
    def run_all_fixes(self):
        """Run all fixes"""
        print("🚀 Starting comprehensive module fixes...\n")
        
        self.fix_websocket_path_issue()
        self.fix_demo_neuroscientist_events()
        self.fix_import_paths()
        self.fix_dashboard_api_path()
        self.fix_event_streaming_imports()
        self.update_requirements_files()
        self.check_and_install_dependencies()
        
        return self.issues_fixed

def main():
    fixer = ModuleFixer()
    issues_fixed = fixer.run_all_fixes()
    
    print("\n" + "="*60)
    print("📋 MODULE FIX REPORT")
    print("="*60)
    
    if issues_fixed:
        print(f"\n✅ Fixed {len(issues_fixed)} issues:\n")
        for i, issue in enumerate(issues_fixed, 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✨ No issues found - all modules appear to be working correctly!")
    
    print("\n" + "="*60)
    print("🎯 RECOMMENDATIONS:")
    print("="*60)
    print("1. Run 'pip install -r auren/requirements.txt' to ensure all dependencies")
    print("2. Set PYTHONPATH before running: export PYTHONPATH=$PYTHONPATH:$(pwd)")
    print("3. Use the auren.sh script for easier management")
    print("4. Consider deploying to production for better stability")
    print("\n✅ Module sweep complete!")

if __name__ == "__main__":
    main() 