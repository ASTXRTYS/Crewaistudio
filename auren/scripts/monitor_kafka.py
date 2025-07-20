#!/usr/bin/env python3
"""
Simple monitoring script to verify Kafka infrastructure health.

Run this before starting CEP implementation to ensure all systems are operational.
"""

import sys
import time
from datetime import datetime

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.monitoring.health import HealthMonitor


def main():
    print("=" * 60)
    print("AUREN Kafka Infrastructure Health Monitor")
    print("=" * 60)
    
    monitor = HealthMonitor()
    
    print("Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        monitor.start_monitoring(interval_seconds=30)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        print("=" * 60)


if __name__ == "__main__":
    main()
