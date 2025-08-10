#!/usr/bin/env python3
"""
VNC Server with noVNC integration for running Chromium
"""
import os
import signal
import subprocess
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import websockify

class VNCServer:
    def __init__(self):
        self.display = ":1"
        self.vnc_port = 5900
        self.web_port = 8080
        self.websocket_port = 6080
        self.screen_resolution = "1280x720"
        
        # Process references
        self.xvfb_process = None
        self.vnc_process = None
        self.chromium_process = None
        self.websockify_process = None
        self.http_server = None
        
    def cleanup_existing_processes(self):
        """Kill existing VNC and X11 processes"""
        try:
            # Kill existing processes
            subprocess.run(['pkill', '-f', 'Xvfb'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'x11vnc'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'chromium'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'websockify'], stderr=subprocess.DEVNULL)
            time.sleep(2)
        except Exception as e:
            print(f"Error cleaning up processes: {e}")
    
    def start_xvfb(self):
        """Start virtual X11 display"""
        try:
            print(f"Starting Xvfb on display {self.display}...")
            
            cmd = [
                "Xvfb", 
                self.display,
                "-screen", "0", f"{self.screen_resolution}x24",
                "-dpi", "96",
                "-ac",
                "+extension", "GLX",
                "+render",
                "-nolisten", "tcp"
            ]
            
            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Set DISPLAY environment variable
            os.environ["DISPLAY"] = self.display
            
            # Wait for X11 to start
            time.sleep(3)
            print(f"✓ Xvfb started on display {self.display}")
            return True
            
        except Exception as e:
            print(f"✗ Error starting Xvfb: {e}")
            return False
    
    def start_vnc_server(self):
        """Start VNC server"""
        try:
            print(f"Starting VNC server on port {self.vnc_port}...")
            
            cmd = [
                "x11vnc",
                "-display", self.display,
                "-forever",
                "-usepw",
                "-create",
                "-nopw",
                "-listen", "localhost",
                "-rfbport", str(self.vnc_port),
                "-shared",
                "-noxdamage",
                "-noxfixes",
                "-noxinerama",
                "-bg"  # Run in background
            ]
            
            # Start VNC server
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"VNC server error: {result.stderr}")
                return False
            
            time.sleep(2)
            print(f"✓ VNC server started on port {self.vnc_port}")
            return True
            
        except Exception as e:
            print(f"✗ Error starting VNC server: {e}")
            return False
    
    def start_websockify(self):
        """Start websockify to bridge WebSocket to VNC"""
        try:
            print(f"Starting websockify on port {self.websocket_port}...")
            
            cmd = [
                "websockify", 
                f"--web=./noVNC",
                f"{self.websocket_port}",
                f"localhost:{self.vnc_port}"
            ]
            
            self.websockify_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(2)
            print(f"✓ websockify started on port {self.websocket_port}")
            return True
            
        except Exception as e:
            print(f"✗ Error starting websockify: {e}")
            return False
    
    def start_chromium(self):
        """Start Chromium browser"""
        try:
            print("Starting Chromium browser...")
            
            # Chrome options for headless VNC operation
            chrome_options = [
                "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                f"--window-size={self.screen_resolution.replace('x', ',')}",
                "--start-maximized",
                "--force-device-scale-factor=1",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--remote-debugging-port=9222",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                f"--user-data-dir=/tmp/chrome-data-{os.getpid()}",
                "--homepage=https://www.google.com"
            ]
            
            # Set display environment
            env = os.environ.copy()
            env["DISPLAY"] = self.display
            
            self.chromium_process = subprocess.Popen(
                chrome_options,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(5)  # Wait for Chrome to start
            print("✓ Chromium browser started successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error starting Chromium: {e}")
            return False
    
    def start_http_server(self):
        """Start HTTP server for noVNC"""
        try:
            print(f"Starting HTTP server on port {self.web_port}...")
            
            def run_server():
                class CustomHandler(SimpleHTTPRequestHandler):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, directory=".", **kwargs)
                
                with socketserver.TCPServer(("", self.web_port), CustomHandler) as httpd:
                    self.http_server = httpd
                    httpd.serve_forever()
            
            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            
            time.sleep(1)
            print(f"✓ HTTP server started on http://localhost:{self.web_port}")
            return True
            
        except Exception as e:
            print(f"✗ Error starting HTTP server: {e}")
            return False
    
    def start_all_services(self):
        """Start all VNC services"""
        print("=" * 50)
        print("🚀 Starting VNC Server with noVNC")
        print("=" * 50)
        
        # Clean up any existing processes
        self.cleanup_existing_processes()
        
        # Start services in order
        if not self.start_xvfb():
            return False
            
        if not self.start_vnc_server():
            return False
            
        if not self.start_chromium():
            return False
            
        if not self.start_websockify():
            return False
            
        if not self.start_http_server():
            return False
        
        print("=" * 50)
        print("✅ All services started successfully!")
        print("=" * 50)
        print(f"🌐 Open your browser and go to:")
        print(f"   http://localhost:{self.web_port}/noVNC/vnc.html?host=localhost&port={self.websocket_port}")
        print(f"   or")  
        print(f"   http://localhost:{self.web_port}/noVNC/vnc_lite.html?host=localhost&port={self.websocket_port}")
        print("=" * 50)
        
        return True
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n🧹 Cleaning up processes...")
        
        processes = [
            (self.chromium_process, "Chromium"),
            (self.websockify_process, "websockify"), 
            (self.vnc_process, "VNC server"),
            (self.xvfb_process, "Xvfb")
        ]
        
        for process, name in processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✓ {name} terminated")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"✓ {name} killed (forced)")
                except Exception as e:
                    print(f"✗ Error stopping {name}: {e}")
        
        # Kill any remaining processes
        self.cleanup_existing_processes()
        print("✓ Cleanup completed")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Received interrupt signal...")
    if 'vnc_server' in globals():
        vnc_server.cleanup()
    exit(0)

def main():
    global vnc_server
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    vnc_server = VNCServer()
    
    try:
        if vnc_server.start_all_services():
            print("\n🎯 VNC server is running. Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
        else:
            print("❌ Failed to start VNC services")
            return 1
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        vnc_server.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())