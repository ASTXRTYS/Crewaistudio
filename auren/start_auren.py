#!/usr/bin/env python3
"""
AUREN 2.0 Startup Script
Complete biometric optimization system with WhatsApp integration
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app import AUREN2App

def setup_environment():
    """Setup environment and directories"""
    
    print("🚀 AUREN 2.0 - Initializing...")
    
    # Create necessary directories
    directories = [
        "/auren/data/conversations",
        "/auren/data/biometrics", 
        "/auren/data/protocols",
        "/auren/data/media",
        "/auren/data/vectors",
        "/auren/logs/system",
        "/auren/logs/biometric",
        "/auren/logs/whatsapp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   Some features may not work without these variables.")
    else:
        print("✅ All required environment variables found")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/auren/logs/system/startup.log'),
            logging.StreamHandler()
        ]
    )

def print_banner():
    """Print AUREN 2.0 banner"""
    
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    AUREN 2.0                                ║
    ║              Biometric Optimization System                   ║
    ║                                                              ║
    ║  • Journal Protocol (Peptide Tracking)                     ║
    ║  • MIRAGE Protocol (Visual Biometrics)                     ║
    ║  • VISOR Protocol (Media Registry)                          ║
    ║  • Agentic RAG (Intelligent Retrieval)                     ║
    ║  • WhatsApp Integration (Mobile Interface)                  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    
    print(banner)

def print_status():
    """Print system status"""
    
    print("\n📊 System Status:")
    print("   • Protocols: Journal, MIRAGE, VISOR")
    print("   • Biometric Analysis: Facial landmark detection")
    print("   • Alert Management: Real-time monitoring")
    print("   • CrewAI Agents: Multi-agent coordination")
    print("   • Agentic RAG: Intelligent information retrieval")
    print("   • WhatsApp: Mobile interface ready")
    
    print("\n🔧 Available Endpoints:")
    print("   • GET  / - System status")
    print("   • GET  /health - Health check")
    print("   • POST /api/protocols/{protocol}/entry - Create protocol entry")
    print("   • POST /api/biometric/analyze - Analyze biometrics")
    print("   • POST /api/convergence/analyze - Convergence analysis")
    print("   • POST /api/crew/process - Process with AI crew")
    print("   • POST /api/rag/query - Query RAG system")
    print("   • POST /api/whatsapp/webhook - WhatsApp webhook")
    print("   • POST /api/whatsapp/send - Send WhatsApp message")

def main():
    """Main startup function"""
    
    try:
        # Print banner
        print_banner()
        
        # Setup environment
        setup_environment()
        
        # Print status
        print_status()
        
        # Start the application
        print(f"\n🚀 Starting AUREN 2.0 at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("   Server will be available at: http://localhost:8000")
        print("   API documentation: http://localhost:8000/docs")
        print("\n   Press Ctrl+C to stop the server")
        
        # Create and run the application
        app = AUREN2App()
        app.run(host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n\n🛑 AUREN 2.0 stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting AUREN 2.0: {e}")
        logging.error(f"Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 