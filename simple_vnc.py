#!/usr/bin/env python3
"""
Simple VNC server - displays Chromium through VNC only
"""
import asyncio
import websockets
import json
import subprocess
import os
import signal
import time
from vnc_server import VNCServer
from browser_manager import BrowserManager
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

class SimpleVNCServer:
    def __init__(self):
        self.vnc_server = VNCServer()
        self.browser_manager = BrowserManager()
        self.clients = set()
        
    async def start_services(self):
        """Start VNC server and browser"""
        try:
            print("Starting Xvfb...")
            self.vnc_server.start_xvfb()
            time.sleep(2)
            
            print("Starting VNC server...")
            self.vnc_server.start_vnc_server()
            time.sleep(2)
            
            print("Starting Chromium...")
            self.browser_manager.start_browser()
            time.sleep(3)
            
            print("All VNC services started successfully")
            return True
        except Exception as e:
            print(f"Error starting services: {e}")
            return False
    
    def start_http_server(self):
        """Start HTTP server for static files"""
        def run_server():
            os.chdir('static')
            handler = SimpleHTTPRequestHandler
            httpd = HTTPServer(("0.0.0.0", 5000), handler)
            print("HTTP server started on http://0.0.0.0:5000")
            httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
    
    async def handle_client(self, websocket):
        """Handle WebSocket connections"""
        self.clients.add(websocket)
        print(f"VNC client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send connection status
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected'
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_vnc_message(data, websocket)
                except json.JSONDecodeError:
                    print("Invalid JSON received")
                except Exception as e:
                    print(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("VNC client disconnected")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_vnc_message(self, data, websocket):
        """Handle VNC-related messages"""
        msg_type = data.get('type')
        
        if msg_type == 'request_screenshot':
            # Take screenshot and send back
            screenshot = self.vnc_server.take_screenshot()
            if screenshot:
                await websocket.send(json.dumps({
                    'type': 'vnc_data',
                    'data': screenshot
                }))
        
        elif msg_type == 'mouse_event':
            # Handle mouse events through VNC
            x = data.get('x', 0)
            y = data.get('y', 0)
            buttons = data.get('buttons', 0)
            self.vnc_server.send_mouse_event(x, y, buttons)
        
        elif msg_type == 'key_event':
            # Handle keyboard events through VNC
            key = data.get('key', '')
            pressed = data.get('pressed', True)
            self.vnc_server.send_key_event(key, pressed)
    
    def cleanup(self):
        """Cleanup all services"""
        print("Cleaning up VNC services...")
        self.vnc_server.cleanup()
        self.browser_manager.cleanup()

async def main():
    server = SimpleVNCServer()
    
    try:
        # Start services
        if not await server.start_services():
            print("Failed to start services")
            return
        
        # Start HTTP server
        server.start_http_server()
        
        # Start WebSocket server for VNC
        print("Starting VNC WebSocket server...")
        async with websockets.serve(
            server.handle_client, 
            "0.0.0.0", 
            8000,
            ping_interval=None,
            ping_timeout=None
        ):
            print("VNC WebSocket server running on ws://0.0.0.0:8000")
            await asyncio.Future()  # Run forever
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())