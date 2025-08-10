#!/usr/bin/env python3
"""
Simple VNC launcher using Python websockify
"""
import subprocess
import time
import os
import signal
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

def run_websockify():
    """Run simple websockify server"""
    try:
        cmd = ["python", "simple_websockify.py"]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"Error starting websockify: {e}")
        return None

def main():
    print("🚀 Starting VNC services...")
    
    # Clean up existing processes
    subprocess.run(['pkill', '-f', 'Xvfb'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'x11vnc'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'chromium'], stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    # Start Xvfb
    print("Starting Xvfb...")
    xvfb = subprocess.Popen([
        "Xvfb", ":1", 
        "-screen", "0", "1280x720x24",
        "-dpi", "96", "-ac"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    os.environ["DISPLAY"] = ":1"
    time.sleep(2)
    
    # Start VNC server
    print("Starting VNC server...")
    vnc = subprocess.run([
        "x11vnc", "-display", ":1",
        "-forever", "-nopw", 
        "-listen", "localhost",
        "-rfbport", "5900",
        "-shared", "-bg"
    ], capture_output=True, text=True)
    
    time.sleep(2)
    
    # Start Chromium
    print("Starting Chromium...")
    chromium = subprocess.Popen([
        "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
        "--no-sandbox", "--disable-dev-shm-usage",
        "--window-size=1280,720", "--start-maximized",
        "https://www.google.com"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(3)
    
    # Start websockify
    print("Starting websockify...")
    websockify_proc = run_websockify()
    if not websockify_proc:
        print("❌ Failed to start websockify")
        return 1
    
    time.sleep(2)
    
    # Start HTTP server
    print("Starting HTTP server...")
    def run_http_server():
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
        
        with socketserver.TCPServer(("", 8080), Handler) as httpd:
            httpd.serve_forever()
    
    server_thread = threading.Thread(target=run_http_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("✅ All services started!")
    print("🌐 Open: http://localhost:8080/noVNC/vnc_lite.html?host=localhost&port=6080")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🧹 Cleaning up...")
        for proc in [xvfb, chromium, websockify_proc]:
            if proc and proc.poll() is None:
                proc.terminate()

if __name__ == "__main__":
    main()