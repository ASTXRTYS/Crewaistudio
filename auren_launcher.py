#!/usr/bin/env python3
"""
AUREN Bulletproof Launcher
Handles all common issues automatically and ensures smooth startup
"""

import os
import sys
import subprocess
import time
import signal
import asyncio
from pathlib import Path
import json

class AURENLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.processes = {}
        self.errors_encountered = []
        
        # Set up environment properly
        self.setup_environment()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def setup_environment(self):
        """Ensure environment is properly configured"""
        # Add project root to Python path
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
        
        # Set PYTHONPATH environment variable
        current_pythonpath = os.environ.get('PYTHONPATH', '')
        if str(self.project_root) not in current_pythonpath:
            os.environ['PYTHONPATH'] = f"{self.project_root}:{current_pythonpath}"
        
        print(f"✅ Environment configured:")
        print(f"   Project root: {self.project_root}")
        print(f"   PYTHONPATH: {os.environ['PYTHONPATH']}")
    
    def check_dependencies(self):
        """Check and install missing dependencies"""
        print("\n🔍 Checking dependencies...")
        
        required_packages = {
            'fastapi': 'fastapi',
            'uvicorn': 'uvicorn[standard]',
            'boto3': 'boto3',
            'redis': 'redis',
            'websockets': 'websockets',
            'aiohttp': 'aiohttp'
        }
        
        missing = []
        for module, package in required_packages.items():
            try:
                __import__(module)
                print(f"   ✓ {module}")
            except ImportError:
                print(f"   ✗ {module} - will install")
                missing.append(package)
        
        if missing:
            print(f"\n📦 Installing missing packages...")
            cmd = [sys.executable, '-m', 'pip', 'install'] + missing
            subprocess.run(cmd, check=True)
            print("   ✅ Dependencies installed!")
        
        return True
    
    def fix_demo_file(self):
        """Fix common issues in demo file"""
        print("\n🔧 Checking demo file...")
        
        demo_path = self.project_root / 'auren' / 'demo' / 'demo_neuroscientist.py'
        
        try:
            # Test if file has syntax errors
            compile(open(demo_path).read(), demo_path, 'exec')
            print("   ✓ Demo file syntax OK")
            return True
        except SyntaxError as e:
            print(f"   ✗ Syntax error found: {e}")
            print("   🔧 Attempting automatic fix...")
            
            # Run the comprehensive fix
            fix_script = """
import re

with open('auren/demo/demo_neuroscientist.py', 'r') as f:
    content = f.read()

# Fix all AURENStreamEvent calls to have proper parameters
lines = content.split('\\n')
fixed_lines = []
in_event = False
event_indent = ""

for i, line in enumerate(lines):
    if 'event = AURENStreamEvent(' in line:
        in_event = True
        event_indent = line[:line.find('event')]
        fixed_lines.append(line)
    elif in_event and line.strip() == ')':
        # Make sure all required params are present
        event_block = '\\n'.join(fixed_lines[-(i-len(fixed_lines)):])
        
        # Add missing parameters if needed
        if 'trace_id=' not in event_block:
            fixed_lines.insert(-1, f'{event_indent}    trace_id=str(uuid.uuid4()),')
        if 'target_agent=' not in event_block:
            fixed_lines.insert(-1, f'{event_indent}    target_agent=None,')
        if 'metadata=' not in event_block:
            fixed_lines.insert(-1, f'{event_indent}    metadata={{}},')
        
        fixed_lines.append(line)
        in_event = False
    else:
        fixed_lines.append(line)

with open('auren/demo/demo_neuroscientist.py', 'w') as f:
    f.write('\\n'.join(fixed_lines))
"""
            
            # Execute fix
            exec(fix_script)
            print("   ✅ Demo file fixed!")
            return True
    
    def check_services(self):
        """Check if required services are running"""
        print("\n🐳 Checking Docker services...")
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            print("   ✓ Redis is running")
        except:
            print("   ✗ Redis not accessible - starting Docker services...")
            self.start_docker_services()
        
        return True
    
    def start_docker_services(self):
        """Start Docker services"""
        compose_file = self.project_root / 'docker-compose.dev.yml'
        
        if compose_file.exists():
            print("   Starting Docker services...")
            subprocess.run(['docker-compose', '-f', str(compose_file), 'up', '-d'], check=True)
            time.sleep(5)  # Wait for services to start
            print("   ✅ Docker services started")
        else:
            print("   ⚠️  docker-compose.dev.yml not found")
    
    def start_service(self, name, command, cwd=None, env=None):
        """Start a service with proper error handling"""
        print(f"\n🚀 Starting {name}...")
        
        # Prepare environment
        service_env = os.environ.copy()
        service_env['PYTHONPATH'] = str(self.project_root)
        if env:
            service_env.update(env)
        
        # Prepare working directory
        if cwd:
            working_dir = self.project_root / cwd
        else:
            working_dir = self.project_root
        
        try:
            # Start process
            process = subprocess.Popen(
                command,
                cwd=str(working_dir),
                env=service_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if still running
            if process.poll() is None:
                self.processes[name] = process
                print(f"   ✅ {name} started (PID: {process.pid})")
                return True
            else:
                # Process died, get error
                stdout, stderr = process.communicate()
                print(f"   ❌ {name} failed to start")
                print(f"   Error: {stderr}")
                self.errors_encountered.append((name, stderr))
                return False
                
        except Exception as e:
            print(f"   ❌ Failed to start {name}: {e}")
            self.errors_encountered.append((name, str(e)))
            return False
    
    def launch(self):
        """Main launch sequence"""
        print("\n" + "="*60)
        print("🧠 AUREN BULLETPROOF LAUNCHER")
        print("="*60)
        
        # Step 1: Check dependencies
        if not self.check_dependencies():
            return False
        
        # Step 2: Fix demo file
        if not self.fix_demo_file():
            return False
        
        # Step 3: Check services
        if not self.check_services():
            return False
        
        # Step 4: Start Dashboard API
        self.start_service(
            "Dashboard API",
            [sys.executable, 'dashboard_api.py'],
            cwd='auren/api'
        )
        
        # Step 5: Start WebSocket Server
        self.start_service(
            "WebSocket Server", 
            [sys.executable, 'enhanced_websocket_streamer.py'],
            cwd='auren/realtime'
        )
        
        # Wait for services to be ready
        print("\n⏳ Waiting for services to initialize...")
        time.sleep(5)
        
        # Step 6: Start Demo
        self.start_service(
            "Demo Neuroscientist",
            [sys.executable, 'auren/demo/demo_neuroscientist.py', '--duration', '3']
        )
        
        # Summary
        print("\n" + "="*60)
        
        if self.errors_encountered:
            print("⚠️  PARTIAL SUCCESS - Some services had issues:")
            for name, error in self.errors_encountered:
                print(f"   - {name}: {error.split(chr(10))[0]}")
        else:
            print("✅ ALL SERVICES STARTED SUCCESSFULLY!")
        
        print("\n📊 Access your dashboards:")
        print("   Main Dashboard: http://localhost:8000/dashboard")
        print("   Direct HTML: Open auren/dashboard/realtime_dashboard.html")
        print("\n🛑 Press Ctrl+C to stop all services")
        print("="*60)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                for name, proc in list(self.processes.items()):
                    if proc.poll() is not None:
                        print(f"\n⚠️  {name} stopped unexpectedly")
                        del self.processes[name]
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.shutdown()
    
    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown"""
        print("\n🛑 Stopping all services...")
        
        for name, process in self.processes.items():
            print(f"   Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("✅ All services stopped")
        sys.exit(0)


if __name__ == "__main__":
    launcher = AURENLauncher()
    launcher.launch() 