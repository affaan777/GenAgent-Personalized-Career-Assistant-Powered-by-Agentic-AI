#!/usr/bin/env python3
"""
GenAgent Startup Script
Launches FastAPI backend and Streamlit frontend only (Chainlit removed)
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

class GenAgentLauncher:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_backend(self):
        """Start FastAPI backend"""
        print("🚀 Starting FastAPI Backend...")
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
            ])
            self.processes.append(("Backend", process))
            print("✅ Backend started at http://localhost:8000")
            return process
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return None
    
    def start_streamlit(self):
        """Start Streamlit frontend"""
        print("🎨 Starting Streamlit Frontend...")
        try:
            # Change to frontend directory
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print("❌ Frontend directory not found. Creating...")
                frontend_dir.mkdir(exist_ok=True)
                print("⚠️  Please add your Streamlit app to frontend/app.py")
                return None
            
            process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "frontend/app.py", "--server.port", "8501", "--server.headless", "true"
            ])
            self.processes.append(("Streamlit", process))
            print("✅ Streamlit started at http://localhost:8501")
            return process
        except Exception as e:
            print(f"❌ Failed to start Streamlit: {e}")
            return None
    
    def check_dependencies(self):
        """Check if required packages are installed"""
        # Core packages that are essential
        core_packages = {
            'backend': ['fastapi', 'uvicorn'],
            'frontend': ['streamlit']
        }
        
        # Optional packages that enhance functionality
        optional_packages = {
            'backend': ['openrouter' 'crewai', 'faiss-cpu', 'transformers'],
            'frontend': ['requests', 'pandas']
        }
        
        missing_core = []
        missing_optional = []
        
        # Check core packages
        for component, packages in core_packages.items():
            for package in packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_core.append(f"{package} (for {component})")
        
        # Check optional packages
        for component, packages in optional_packages.items():
            for package in packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_optional.append(f"{package} (for {component})")
        
        # Report missing packages
        if missing_core:
            print("❌ Missing essential packages:")
            for package in missing_core:
                print(f"   - {package}")
            print("\nInstall with:")
            print("   pip install -r requirements.txt")
            return False
        
        if missing_optional:
            print("⚠️  Missing optional packages (some features may not work):")
            for package in missing_optional:
                print(f"   - {package}")
            print("\nFor full functionality, install:")
            print("   pip install -r requirements.txt")
            print("\nContinuing with available packages...")
        
        return True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down GenAgent...")
        self.running = False
        self.stop_all()
        sys.exit(0)
    
    def stop_all(self):
        """Stop all running processes"""
        for name, process in self.processes:
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            for name, process in self.processes[:]:
                if process.poll() is not None:
                    print(f"⚠️  {name} process stopped unexpectedly")
                    self.processes.remove((name, process))
            time.sleep(2)
    
    def run(self):
        """Main launcher method (Chainlit removed)"""
        print("🧠 GenAgent Launcher")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            return
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start components
        backend_process = self.start_backend()
        if not backend_process:
            print("❌ Cannot start without backend")
            return
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        streamlit_process = self.start_streamlit()
        if not streamlit_process:
            print("⚠️  Streamlit not started - check frontend/app.py")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Display status
        print("\n" + "=" * 50)
        print("🎉 GenAgent is running!")
        print("\n📱 Access Points:")
        print("   Backend API:  http://localhost:8000")
        print("   API Docs:     http://localhost:8000/docs")
        if streamlit_process:
            print("   Streamlit UI: http://localhost:8501")
        print("\n🛑 Press Ctrl+C to stop all services")
        print("=" * 50)
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch GenAgent components")
    parser.add_argument("--backend-only", action="store_true", help="Start only backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only frontend")
    
    args = parser.parse_args()
    
    launcher = GenAgentLauncher()
    
    if args.backend_only:
        print("🚀 Starting Backend Only...")
        launcher.start_backend()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop_all()
    elif args.frontend_only:
        print("🎨 Starting Frontend Only...")
        launcher.start_streamlit()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop_all()
    else:
        launcher.run()

if __name__ == "__main__":
    main() 