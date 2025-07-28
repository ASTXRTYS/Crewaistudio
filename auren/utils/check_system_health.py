#!/usr/bin/env python3
"""
AUREN System Health Check
Comprehensive verification that all components are operational
"""

import asyncio
import sys
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import json
import aiohttp
import redis.asyncio as redis
import asyncpg
import psutil

# Try imports to check if packages are installed
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class SystemHealthChecker:
    """Comprehensive health checker for AUREN system"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.results = []
        
    async def run_all_checks(self) -> bool:
        """Run all system health checks"""
        print(f"\n{Colors.BOLD}🏥 AUREN SYSTEM HEALTH CHECK{Colors.ENDC}")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")
        
        # Define all checks
        checks = [
            ("Docker Services", self.check_docker_services),
            ("Redis Connectivity", self.check_redis),
            ("PostgreSQL Connectivity", self.check_postgres),
            ("Event Streams", self.check_event_streams),
            ("Dashboard API", self.check_dashboard_api),
            ("WebSocket Server", self.check_websocket),
            ("S3/LocalStack", self.check_s3),
            ("System Resources", self.check_system_resources),
            ("Python Dependencies", self.check_python_dependencies),
            ("Directory Structure", self.check_directory_structure)
        ]
        
        # Run each check
        for name, check_func in checks:
            print(f"{Colors.BLUE}Checking {name}...{Colors.ENDC}")
            success, message, details = await self._run_check(name, check_func)
            
            self.results.append({
                "component": name,
                "success": success,
                "message": message,
                "details": details
            })
            
            if success:
                self.checks_passed += 1
                print(f"{Colors.GREEN}✅ {name}{Colors.ENDC}: {message}")
            elif success is None:  # Warning
                self.warnings += 1
                print(f"{Colors.YELLOW}⚠️  {name}{Colors.ENDC}: {message}")
            else:
                self.checks_failed += 1
                print(f"{Colors.RED}❌ {name}{Colors.ENDC}: {message}")
            
            if details:
                for detail in details:
                    print(f"   {Colors.CYAN}→{Colors.ENDC} {detail}")
            print()
        
        # Summary
        self._print_summary()
        
        # Generate report
        await self.generate_health_report()
        
        # Next steps
        if self.checks_failed > 0:
            self._print_remediation_steps()
        
        return self.checks_failed == 0
    
    async def _run_check(self, name: str, check_func) -> Tuple[bool, str, List[str]]:
        """Run a single check with error handling"""
        try:
            return await check_func()
        except Exception as e:
            return False, f"Exception: {str(e)}", []
    
    async def check_docker_services(self) -> Tuple[bool, str, List[str]]:
        """Check if Docker services are running"""
        try:
            # Check if docker-compose.dev.yml exists
            if not os.path.exists("docker-compose.dev.yml"):
                return False, "docker-compose.dev.yml not found", [
                    "Create docker-compose.dev.yml as instructed"
                ]
            
            # Check if Docker is running
            import subprocess
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, "Docker is not running", [
                    "Start Docker Desktop or Docker daemon"
                ]
            
            # Check for running containers
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.dev.yml", "ps"],
                capture_output=True,
                text=True
            )
            
            if "auren-redis-dev" in result.stdout and "auren-postgres-dev" in result.stdout:
                running_services = []
                if "auren-redis-dev" in result.stdout:
                    running_services.append("Redis")
                if "auren-postgres-dev" in result.stdout:
                    running_services.append("PostgreSQL")
                if "auren-localstack-dev" in result.stdout:
                    running_services.append("LocalStack")
                    
                return True, f"Services running: {', '.join(running_services)}", []
            else:
                return None, "Some services not running", [
                    "Run: docker-compose -f docker-compose.dev.yml up -d"
                ]
                
        except FileNotFoundError:
            return False, "Docker not installed", [
                "Install Docker Desktop from https://docker.com"
            ]
        except Exception as e:
            return False, f"Error checking Docker: {str(e)}", []
    
    async def check_redis(self) -> Tuple[bool, str, List[str]]:
        """Check Redis connectivity"""
        try:
            client = redis.from_url("redis://localhost:6379")
            await client.ping()
            
            # Check for event streams
            streams = []
            for tier in ["critical", "operational", "analytical"]:
                key = f"auren:events:{tier}"
                try:
                    length = await client.xlen(key)
                    if length > 0:
                        streams.append(f"{tier}: {length} events")
                except:
                    pass
            
            await client.close()
            
            if streams:
                return True, "Connected", streams
            else:
                return True, "Connected (no event streams yet)", []
                
        except Exception as e:
            return False, f"Cannot connect to Redis", [
                "Ensure Redis is running on port 6379",
                "Check: docker ps | grep redis"
            ]
    
    async def check_postgres(self) -> Tuple[bool, str, List[str]]:
        """Check PostgreSQL connectivity"""
        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                user="auren",
                password="auren_dev_password",
                database="auren_dev"
            )
            
            # Check for required tables
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            
            table_names = [t['tablename'] for t in tables]
            required_tables = ['events', 'agent_memories', 'hypotheses', 'learning_progress']
            
            missing_tables = [t for t in required_tables if t not in table_names]
            
            await conn.close()
            
            if missing_tables:
                return None, "Connected but missing tables", [
                    f"Missing: {', '.join(missing_tables)}",
                    "Tables will be created on first startup"
                ]
            else:
                return True, f"Connected with {len(table_names)} tables", []
                
        except Exception as e:
            return False, f"Cannot connect to PostgreSQL", [
                "Ensure PostgreSQL is running on port 5432",
                "Check credentials in docker-compose.dev.yml"
            ]
    
    async def check_event_streams(self) -> Tuple[bool, str, List[str]]:
        """Check event streaming infrastructure"""
        try:
            # Check if instrumentation module exists
            from auren.realtime.langgraph_instrumentation import CrewAIEventInstrumentation
            
            # Check if streaming module exists
            from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
            
            return True, "Event streaming modules available", [
                "CrewAI instrumentation ready",
                "Multi-protocol streaming ready"
            ]
            
        except ImportError as e:
            return False, "Event streaming modules not found", [
                f"Missing module: {str(e)}",
                "Check auren/realtime/ directory"
            ]
    
    async def check_dashboard_api(self) -> Tuple[bool, str, List[str]]:
        """Check Dashboard API availability"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        components = data.get('components', {})
                        healthy_components = [k for k, v in components.items() if v == 'healthy']
                        
                        return True, "API running", [
                            f"Healthy components: {len(healthy_components)}",
                            f"WebSocket connections: {data.get('active_websocket_connections', 0)}"
                        ]
                    else:
                        return False, f"API returned status {resp.status}", []
                        
        except aiohttp.ClientError:
            return None, "API not running", [
                "Start with: python auren/api/dashboard_api.py",
                "Or: uvicorn auren.api.dashboard_api:app --reload"
            ]
        except Exception as e:
            return False, f"Error checking API: {str(e)}", []
    
    async def check_websocket(self) -> Tuple[bool, str, List[str]]:
        """Check WebSocket server"""
        try:
            # Try to connect to WebSocket
            import websockets
            
            uri = "ws://localhost:8765"
            async with websockets.connect(uri) as websocket:
                # Send subscription message
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "filters": {
                        "event_types": ["system_health"],
                        "priority": "critical"
                    }
                }))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    return True, "WebSocket server responding", []
                except asyncio.TimeoutError:
                    return True, "WebSocket connected (no events)", []
                    
        except Exception:
            return None, "WebSocket server not running", [
                "Start with: python auren/realtime/enhanced_websocket_streamer.py"
            ]
    
    async def check_s3(self) -> Tuple[bool, str, List[str]]:
        """Check S3/LocalStack availability"""
        if not BOTO3_AVAILABLE:
            return None, "boto3 not installed", [
                "Install with: pip install boto3"
            ]
            
        try:
            import boto3
            
            # Create S3 client for LocalStack
            s3_client = boto3.client(
                's3',
                endpoint_url='http://localhost:4566',
                aws_access_key_id='test',
                aws_secret_access_key='test',
                region_name='us-east-1'
            )
            
            # List buckets
            response = s3_client.list_buckets()
            buckets = [b['Name'] for b in response.get('Buckets', [])]
            
            if 'auren-events' in buckets:
                return True, "LocalStack S3 ready", [
                    f"Buckets: {', '.join(buckets)}"
                ]
            else:
                return None, "LocalStack running but bucket missing", [
                    "Create bucket: aws --endpoint-url=http://localhost:4566 s3 mb s3://auren-events"
                ]
                
        except Exception:
            return None, "LocalStack not running", [
                "LocalStack provides S3 for local testing",
                "Start with: docker-compose -f docker-compose.dev.yml up localstack"
            ]
    
    async def check_system_resources(self) -> Tuple[bool, str, List[str]]:
        """Check system resource availability"""
        # CPU check
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory check
        memory = psutil.virtual_memory()
        memory_available_gb = memory.available / (1024**3)
        
        # Disk check
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024**3)
        
        details = [
            f"CPU Usage: {cpu_percent}%",
            f"Memory Available: {memory_available_gb:.1f} GB ({memory.percent}% used)",
            f"Disk Free: {disk_free_gb:.1f} GB ({disk.percent}% used)"
        ]
        
        # Determine status
        if memory_available_gb < 2 or disk_free_gb < 5:
            return None, "Low resources", details + [
                "Recommended: 4GB+ RAM, 10GB+ free disk"
            ]
        else:
            return True, "Adequate resources", details
    
    async def check_python_dependencies(self) -> Tuple[bool, str, List[str]]:
        """Check required Python packages"""
        required_packages = [
            "crewai",
            "redis",
            "asyncpg",
            "fastapi",
            "websockets",
            "boto3",
            "psutil"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            return False, f"Missing {len(missing)} packages", [
                f"Missing: {', '.join(missing)}",
                "Install with: pip install -r auren/requirements.txt"
            ]
        else:
            return True, f"All {len(required_packages)} required packages installed", []
    
    async def check_directory_structure(self) -> Tuple[bool, str, List[str]]:
        """Check required directory structure"""
        required_dirs = [
            "auren/api",
            "auren/realtime",
            "auren/dashboard",
            "auren/demo",
            "auren/utils",
            "sql/init"
        ]
        
        missing = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing.append(dir_path)
        
        if missing:
            return None, f"Missing {len(missing)} directories", [
                f"Missing: {', '.join(missing)}",
                "These will be created as needed"
            ]
        else:
            return True, "All required directories present", []
    
    def _print_summary(self):
        """Print health check summary"""
        total = self.checks_passed + self.checks_failed + self.warnings
        
        print(f"\n{Colors.BOLD}📊 SUMMARY{Colors.ENDC}")
        print("=" * 60)
        print(f"{Colors.GREEN}Passed:{Colors.ENDC} {self.checks_passed}/{total}")
        print(f"{Colors.YELLOW}Warnings:{Colors.ENDC} {self.warnings}/{total}")
        print(f"{Colors.RED}Failed:{Colors.ENDC} {self.checks_failed}/{total}")
        
        if self.checks_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✨ System is healthy and ready!{Colors.ENDC}")
        elif self.checks_failed <= 2:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  System needs minor fixes{Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ System requires attention{Colors.ENDC}")
    
    def _print_remediation_steps(self):
        """Print steps to fix issues"""
        print(f"\n{Colors.BOLD}🔧 REMEDIATION STEPS{Colors.ENDC}")
        print("=" * 60)
        
        print(f"\n{Colors.CYAN}1. Start Docker services:{Colors.ENDC}")
        print("   docker-compose -f docker-compose.dev.yml up -d")
        
        print(f"\n{Colors.CYAN}2. Start the Dashboard API:{Colors.ENDC}")
        print("   python auren/api/dashboard_api.py")
        
        print(f"\n{Colors.CYAN}3. Start the WebSocket server:{Colors.ENDC}")
        print("   python auren/realtime/enhanced_websocket_streamer.py")
        
        print(f"\n{Colors.CYAN}4. Run the demo:{Colors.ENDC}")
        print("   python auren/demo/demo_neuroscientist.py --duration 2")
        
        print(f"\n{Colors.CYAN}5. Open the dashboard:{Colors.ENDC}")
        print("   http://localhost:8000/dashboard")
    
    async def generate_health_report(self):
        """Generate detailed health report file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": len(self.results),
                "passed": self.checks_passed,
                "warnings": self.warnings,
                "failed": self.checks_failed
            },
            "results": self.results,
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3)
            }
        }
        
        # Write report
        report_path = "auren_health_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.CYAN}📄 Detailed report saved:{Colors.ENDC} {report_path}")


async def main():
    """Run system health check"""
    checker = SystemHealthChecker()
    
    try:
        success = await checker.run_all_checks()
        
        # Exit code for scripts
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Health check interrupted{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main()) 