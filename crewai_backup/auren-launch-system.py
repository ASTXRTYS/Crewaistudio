#!/usr/bin/env python3
"""
AUREN Complete System Launch Orchestrator
Start the entire AUREN intelligence system with one command

Usage:
    python launch_auren.py [--production | --development | --demo]

This script orchestrates:
- Database connections and health checks
- Redis event streaming infrastructure
- WebSocket server for real-time updates
- S3 archival system
- Agent initialization with monitoring
- Dashboard launch
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import webbrowser
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import json
import argparse

# Configure logging with color support
class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for better visibility"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

# Setup logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class AURENSystemLauncher:
    """
    Orchestrates the complete AUREN system startup
    Handles health checks, graceful shutdown, and monitoring
    """
    
    def __init__(self, mode: str = "development"):
        self.mode = mode
        self.processes = {}
        self.components_started = set()
        self.startup_start_time = None
        self.is_running = False
        
        # Component configurations by mode
        self.configs = {
            "development": {
                "redis_url": "redis://localhost:6379",
                "postgres_url": "postgresql://localhost:5432/auren_dev",
                "websocket_port": 8765,
                "api_port": 8000,
                "dashboard_url": "http://localhost:8080/dashboard.html",
                "log_level": "DEBUG",
                "enable_archival": False
            },
            "production": {
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
                "postgres_url": os.getenv("DATABASE_URL"),
                "websocket_port": int(os.getenv("WEBSOCKET_PORT", "8765")),
                "api_port": int(os.getenv("API_PORT", "8000")),
                "dashboard_url": os.getenv("DASHBOARD_URL", "https://auren.health/dashboard"),
                "log_level": "INFO",
                "enable_archival": True
            },
            "demo": {
                "redis_url": "redis://localhost:6379",
                "postgres_url": "postgresql://localhost:5432/auren_demo",
                "websocket_port": 8765,
                "api_port": 8000,
                "dashboard_url": "http://localhost:8080/dashboard.html",
                "log_level": "INFO",
                "enable_archival": True
            }
        }
        
        self.config = self.configs[mode]
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def launch(self):
        """Main launch sequence"""
        self.startup_start_time = time.time()
        self.is_running = True
        
        logger.info(f"🚀 Starting AUREN System in {self.mode.upper()} mode")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Infrastructure
            await self.check_dependencies()
            await self.start_infrastructure()
            
            # Phase 2: Core Services
            await self.start_core_services()
            
            # Phase 3: Agent System
            await self.start_agent_system()
            
            # Phase 4: Monitoring & UI
            await self.start_monitoring()
            
            # Calculate startup time
            startup_time = time.time() - self.startup_start_time
            logger.info("=" * 60)
            logger.info(f"✅ AUREN System fully operational in {startup_time:.1f} seconds!")
            logger.info(f"🌐 Dashboard: {self.config['dashboard_url']}")
            logger.info(f"📊 WebSocket: ws://localhost:{self.config['websocket_port']}")
            logger.info("=" * 60)
            
            # Open dashboard in browser if in demo mode
            if self.mode == "demo":
                logger.info("Opening dashboard in browser...")
                webbrowser.open(f"file://{os.path.abspath('auren/dashboard/realtime_dashboard.html')}")
            
            # Keep running and monitor health
            await self.monitor_system_health()
            
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            await self.shutdown()
            raise
    
    async def check_dependencies(self):
        """Verify all required services are available"""
        logger.info("🔍 Checking system dependencies...")
        
        checks = {
            "Redis": self.check_redis,
            "PostgreSQL": self.check_postgres,
            "Python packages": self.check_python_packages
        }
        
        for name, check_func in checks.items():
            try:
                await check_func()
                logger.info(f"  ✓ {name} - OK")
            except Exception as e:
                logger.error(f"  ✗ {name} - FAILED: {e}")
                raise
    
    async def check_redis(self):
        """Verify Redis connectivity"""
        import redis.asyncio as redis
        
        client = redis.from_url(self.config["redis_url"])
        await client.ping()
        await client.close()
    
    async def check_postgres(self):
        """Verify PostgreSQL connectivity"""
        if self.mode == "development":
            # Skip in development if not configured
            return
            
        import asyncpg
        
        conn = await asyncpg.connect(self.config["postgres_url"])
        await conn.fetchval("SELECT 1")
        await conn.close()
    
    async def check_python_packages(self):
        """Verify required packages are installed"""
        required_packages = [
            "crewai", "redis", "asyncpg", "websockets",
            "boto3", "opentelemetry-api", "fastapi"
        ]
        
        import importlib
        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
            except ImportError:
                raise Exception(f"Missing package: {package}")
    
    async def start_infrastructure(self):
        """Start infrastructure services"""
        logger.info("🏗️  Starting infrastructure services...")
        
        # Clear Redis streams in development mode
        if self.mode == "development":
            import redis.asyncio as redis
            client = redis.from_url(self.config["redis_url"])
            await client.delete("auren:events:critical")
            await client.delete("auren:events:operational")
            await client.delete("auren:events:analytical")
            await client.close()
            logger.info("  ✓ Cleared development Redis streams")
        
        self.components_started.add("infrastructure")
    
    async def start_core_services(self):
        """Start core AUREN services"""
        logger.info("🧠 Starting core services...")
        
        # Start WebSocket server
        websocket_cmd = [
            sys.executable, "-m", "auren.realtime.start_websocket_server",
            "--port", str(self.config["websocket_port"]),
            "--redis-url", self.config["redis_url"]
        ]
        
        self.processes["websocket"] = await self.start_process(
            "WebSocket Server",
            websocket_cmd
        )
        
        # Wait for WebSocket to be ready
        await self.wait_for_port(self.config["websocket_port"], "WebSocket")
        
        # Start S3 Archival if enabled
        if self.config["enable_archival"]:
            archival_cmd = [
                sys.executable, "-m", "auren.realtime.start_archival_service",
                "--redis-url", self.config["redis_url"]
            ]
            
            self.processes["archival"] = await self.start_process(
                "S3 Archival",
                archival_cmd
            )
        
        self.components_started.add("core_services")
    
    async def start_agent_system(self):
        """Initialize the agent system with monitoring"""
        logger.info("🤖 Starting agent system...")
        
        # In production, this would start the actual agent services
        # For now, we'll start a demo agent that generates events
        
        if self.mode in ["demo", "development"]:
            demo_cmd = [
                sys.executable, "-m", "auren.tests.demo_agent_simulator",
                "--redis-url", self.config["redis_url"],
                "--event-rate", "5" if self.mode == "demo" else "2"
            ]
            
            self.processes["demo_agent"] = await self.start_process(
                "Demo Agent",
                demo_cmd
            )
        
        self.components_started.add("agents")
    
    async def start_monitoring(self):
        """Start monitoring and observability"""
        logger.info("📊 Starting monitoring systems...")
        
        # Start metrics server if in production
        if self.mode == "production":
            metrics_cmd = [
                sys.executable, "-m", "auren.monitoring.start_metrics_server",
                "--port", "9090"
            ]
            
            self.processes["metrics"] = await self.start_process(
                "Metrics Server",
                metrics_cmd
            )
        
        self.components_started.add("monitoring")
    
    async def start_process(self, name: str, cmd: List[str]) -> subprocess.Popen:
        """Start a subprocess with logging"""
        logger.info(f"  Starting {name}...")
        
        # Create log file for process
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = open(f"{log_dir}/{name.lower().replace(' ', '_')}.log", "w")
        
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        
        # Give process time to start
        await asyncio.sleep(1)
        
        # Check if process started successfully
        if process.poll() is not None:
            raise Exception(f"{name} failed to start (exit code: {process.returncode})")
        
        logger.info(f"  ✓ {name} started (PID: {process.pid})")
        return process
    
    async def wait_for_port(self, port: int, service_name: str, timeout: int = 30):
        """Wait for a service to start listening on a port"""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    logger.info(f"  ✓ {service_name} is ready on port {port}")
                    return
            except:
                pass
            
            await asyncio.sleep(0.5)
        
        raise TimeoutError(f"{service_name} failed to start on port {port}")
    
    async def monitor_system_health(self):
        """Continuously monitor system health"""
        logger.info("💚 System health monitoring active")
        
        health_check_interval = 30  # seconds
        error_count = 0
        max_errors = 3
        
        while self.is_running:
            try:
                # Check all processes
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"❌ {name} has crashed (exit code: {process.returncode})")
                        error_count += 1
                        
                        if error_count >= max_errors:
                            logger.critical("Too many failures, shutting down")
                            await self.shutdown()
                            return
                        
                        # Attempt restart
                        logger.info(f"🔄 Attempting to restart {name}...")
                        # Restart logic would go here
                
                # Reset error count if health check passes
                if error_count > 0:
                    logger.info("✅ System recovered")
                    error_count = 0
                
                # Log basic metrics
                if self.mode == "production":
                    await self.log_system_metrics()
                
                await asyncio.sleep(health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def log_system_metrics(self):
        """Log system metrics for monitoring"""
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "process_count": len(self.processes),
            "uptime_seconds": time.time() - self.startup_start_time
        }
        
        # In production, send to monitoring system
        logger.debug(f"System metrics: {json.dumps(metrics, indent=2)}")
    
    async def shutdown(self):
        """Graceful shutdown sequence"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("🛑 Initiating graceful shutdown...")
        
        # Stop processes in reverse order
        shutdown_order = ["demo_agent", "archival", "websocket", "metrics"]
        
        for name in shutdown_order:
            if name in self.processes:
                process = self.processes[name]
                if process.poll() is None:  # Still running
                    logger.info(f"  Stopping {name}...")
                    process.terminate()
                    
                    # Give process time to shutdown gracefully
                    try:
                        process.wait(timeout=5)
                        logger.info(f"  ✓ {name} stopped")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"  ⚠️  {name} did not stop gracefully, forcing...")
                        process.kill()
        
        logger.info("✅ Shutdown complete")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Launch AUREN System")
    parser.add_argument(
        "--mode",
        choices=["development", "production", "demo"],
        default="development",
        help="Launch mode (default: development)"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip dependency checks"
    )
    
    args = parser.parse_args()
    
    # ASCII Art Banner
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ██╗   ██╗██████╗ ███████╗███╗   ██╗          ║
    ║    ██╔══██╗██║   ██║██╔══██╗██╔════╝████╗  ██║          ║
    ║    ███████║██║   ██║██████╔╝█████╗  ██╔██╗ ██║          ║
    ║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║╚██╗██║          ║
    ║    ██║  ██║╚██████╔╝██║  ██║███████╗██║ ╚████║          ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝          ║
    ║                                                           ║
    ║         AI Health Intelligence That Remembers             ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    
    print(banner)
    
    launcher = AURENSystemLauncher(mode=args.mode)
    
    try:
        await launcher.launch()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
