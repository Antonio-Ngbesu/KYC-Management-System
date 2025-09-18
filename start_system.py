"""
KYC System Startup Script
Automated startup and management script for all system components
"""
import subprocess
import sys
import time
import requests
import signal
import os
import psutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
import argparse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
API_PORT = 8000
UI_PORTS = {
    "customer": 8501,
    "analyst": 8502,
    "admin": 8503,
    "launcher": 8504,
    "test": 8505
}

class KYCSystemManager:
    """Manages the entire KYC system lifecycle"""
    
    def __init__(self):
        self.processes = {}
        self.startup_order = [
            "api",
            "customer",
            "analyst", 
            "admin",
            "launcher"
        ]
        
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            return False  # Port is in use
        except:
            return True  # Port is available
    
    def kill_process_on_port(self, port: int):
        """Kill any process running on specified port"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections']:
                        if conn.laddr.port == port:
                            logger.info(f"Killing process {proc.info['pid']} on port {port}")
                            proc.kill()
                            time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.warning(f"Could not kill process on port {port}: {e}")
    
    def start_api_server(self) -> bool:
        """Start the FastAPI server"""
        logger.info("Starting API server...")
        
        if not self.check_port_available(API_PORT):
            logger.warning(f"Port {API_PORT} is in use, attempting to kill existing process...")
            self.kill_process_on_port(API_PORT)
            time.sleep(2)
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.api.main:app",
                "--host", "0.0.0.0",
                "--port", str(API_PORT),
                "--reload"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.processes["api"] = process
            
            # Wait for API to be ready
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"http://localhost:{API_PORT}/health", timeout=1)
                    if response.status_code == 200:
                        logger.info("✅ API server started successfully")
                        return True
                except:
                    time.sleep(1)
            
            logger.error("❌ API server failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            return False
    
    def start_ui_interface(self, interface_type: str) -> bool:
        """Start a Streamlit UI interface"""
        port = UI_PORTS[interface_type]
        logger.info(f"Starting {interface_type} interface on port {port}...")
        
        if not self.check_port_available(port):
            logger.warning(f"Port {port} is in use, attempting to kill existing process...")
            self.kill_process_on_port(port)
            time.sleep(2)
        
        try:
            # Determine the correct file path
            if interface_type == "customer":
                ui_file = "src/ui/customer_portal.py"
            elif interface_type == "launcher":
                ui_file = "src/ui/system_launcher.py"
            elif interface_type == "test":
                ui_file = "src/ui/test_integration.py"
            else:
                ui_file = f"src/ui/{interface_type}_dashboard.py"
            
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                ui_file,
                "--server.port", str(port),
                "--server.headless", "true",
                "--server.runOnSave", "true"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.processes[interface_type] = process
            
            # Wait for interface to be ready
            for i in range(20):  # Wait up to 20 seconds
                try:
                    response = requests.get(f"http://localhost:{port}", timeout=1)
                    if response.status_code == 200:
                        logger.info(f"✅ {interface_type.title()} interface started successfully")
                        return True
                except:
                    time.sleep(1)
            
            logger.error(f"❌ {interface_type.title()} interface failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start {interface_type} interface: {e}")
            return False
    
    def start_all_services(self) -> bool:
        """Start all system services in order"""
        logger.info("🚀 Starting KYC System...")
        
        success_count = 0
        total_services = len(self.startup_order)
        
        # Start API server first
        if self.start_api_server():
            success_count += 1
        else:
            logger.error("Failed to start API server - aborting startup")
            return False
        
        # Start UI interfaces
        for interface in self.startup_order[1:]:  # Skip 'api' as it's already started
            if self.start_ui_interface(interface):
                success_count += 1
            else:
                logger.warning(f"Failed to start {interface} interface")
        
        logger.info(f"✅ Startup complete: {success_count}/{total_services} services running")
        
        # Print service URLs
        self.print_service_urls()
        
        return success_count == total_services
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("🛑 Stopping all services...")
        
        for service_name, process in self.processes.items():
            try:
                logger.info(f"Stopping {service_name}...")
                if os.name == 'nt':
                    # Windows
                    process.send_signal(signal.CTRL_C_EVENT)
                else:
                    # Unix/Linux
                    process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                logger.info(f"✅ {service_name} stopped")
                
            except Exception as e:
                logger.warning(f"Error stopping {service_name}: {e}")
        
        self.processes.clear()
        logger.info("🛑 All services stopped")
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        logger.info(f"🔄 Restarting {service_name}...")
        
        # Stop the service if running
        if service_name in self.processes:
            try:
                self.processes[service_name].terminate()
                self.processes[service_name].wait(timeout=5)
            except:
                pass
            del self.processes[service_name]
        
        # Restart the service
        if service_name == "api":
            return self.start_api_server()
        else:
            return self.start_ui_interface(service_name)
    
    def get_system_status(self) -> Dict[str, Dict]:
        """Get status of all services"""
        status = {}
        
        # Check API
        try:
            response = requests.get(f"http://localhost:{API_PORT}/health", timeout=2)
            status["api"] = {
                "running": response.status_code == 200,
                "port": API_PORT,
                "url": f"http://localhost:{API_PORT}",
                "docs_url": f"http://localhost:{API_PORT}/docs"
            }
        except:
            status["api"] = {
                "running": False,
                "port": API_PORT,
                "url": f"http://localhost:{API_PORT}",
                "docs_url": f"http://localhost:{API_PORT}/docs"
            }
        
        # Check UI interfaces
        for interface, port in UI_PORTS.items():
            try:
                response = requests.get(f"http://localhost:{port}", timeout=2)
                status[interface] = {
                    "running": response.status_code == 200,
                    "port": port,
                    "url": f"http://localhost:{port}"
                }
            except:
                status[interface] = {
                    "running": False,
                    "port": port,
                    "url": f"http://localhost:{port}"
                }
        
        return status
    
    def print_service_urls(self):
        """Print all service URLs"""
        logger.info("\n" + "="*60)
        logger.info("🌐 KYC System Service URLs")
        logger.info("="*60)
        
        status = self.get_system_status()
        
        for service_name, service_info in status.items():
            status_emoji = "🟢" if service_info["running"] else "🔴"
            service_title = service_name.replace("_", " ").title()
            
            logger.info(f"{status_emoji} {service_title}: {service_info['url']}")
            
            if service_name == "api" and service_info["running"]:
                logger.info(f"   📚 API Documentation: {service_info['docs_url']}")
        
        logger.info("="*60)
    
    def monitor_services(self, check_interval: int = 30):
        """Monitor services and restart if they fail"""
        logger.info(f"🔍 Monitoring services (checking every {check_interval}s)")
        logger.info("Press Ctrl+C to stop monitoring and shutdown services")
        
        try:
            while True:
                status = self.get_system_status()
                failed_services = [name for name, info in status.items() if not info["running"]]
                
                if failed_services:
                    logger.warning(f"⚠️ Failed services detected: {failed_services}")
                    for service in failed_services:
                        if service in self.processes:
                            logger.info(f"🔄 Attempting to restart {service}...")
                            self.restart_service(service)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring interrupted - shutting down services...")
            self.stop_all_services()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KYC System Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "monitor"], 
                       help="Action to perform")
    parser.add_argument("--service", help="Specific service to restart (when using restart)")
    parser.add_argument("--monitor-interval", type=int, default=30, 
                       help="Monitoring check interval in seconds")
    
    args = parser.parse_args()
    
    manager = KYCSystemManager()
    
    if args.action == "start":
        logger.info("🚀 Starting KYC System...")
        success = manager.start_all_services()
        
        if success:
            logger.info("✅ All services started successfully!")
            logger.info("🔍 Starting service monitoring...")
            manager.monitor_services(args.monitor_interval)
        else:
            logger.error("❌ Failed to start all services")
            sys.exit(1)
    
    elif args.action == "stop":
        manager.stop_all_services()
    
    elif args.action == "restart":
        if args.service:
            success = manager.restart_service(args.service)
            if success:
                logger.info(f"✅ Service {args.service} restarted successfully")
            else:
                logger.error(f"❌ Failed to restart service {args.service}")
        else:
            logger.info("🔄 Restarting all services...")
            manager.stop_all_services()
            time.sleep(2)
            manager.start_all_services()
    
    elif args.action == "status":
        status = manager.get_system_status()
        
        print("\n" + "="*60)
        print("📊 KYC System Status")
        print("="*60)
        
        for service_name, service_info in status.items():
            status_emoji = "🟢 RUNNING" if service_info["running"] else "🔴 STOPPED"
            service_title = service_name.replace("_", " ").title()
            
            print(f"{service_title:<20} {status_emoji:<12} Port: {service_info['port']}")
        
        print("="*60)
        
        running_services = sum(1 for info in status.values() if info["running"])
        total_services = len(status)
        
        if running_services == total_services:
            print(f"✅ All {total_services} services are running")
        else:
            print(f"⚠️  {running_services}/{total_services} services running")
    
    elif args.action == "monitor":
        logger.info("🔍 Starting service monitoring...")
        manager.monitor_services(args.monitor_interval)

if __name__ == "__main__":
    main()
