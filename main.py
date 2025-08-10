#!/usr/bin/env python3
"""
Main server for web-based Chromium browser with VNC access
"""
import asyncio
import websockets
import websockets.server
import json
import subprocess
import os
import signal
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
from vnc_server import VNCServer
from browser_manager import BrowserManager

class VNCWebSocketHandler:
    def __init__(self):
        self.vnc_server = VNCServer()
        self.browser_manager = BrowserManager()
        self.clients = set()
        
    async def start_services(self):
        """Start VNC server and browser"""
        try:
            # Start virtual display
            self.vnc_server.start_xvfb()
            time.sleep(2)
            
            # Start VNC server
            self.vnc_server.start_vnc_server()
            time.sleep(2)
            
            # Start Chromium browser
            self.browser_manager.start_browser()
            time.sleep(3)
            
            print("All services started successfully")
            return True
        except Exception as e:
            print(f"Error starting services: {e}")
            return False
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        # Check if this is a WebSocket connection from our VNC client  
        if path != "/ws" and path != "/":
            return
            
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            await self.handle_messages(websocket)
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_messages(self, websocket):
        """Handle WebSocket messages"""
        # Send initial connection success message
        await websocket.send(json.dumps({
            'type': 'connection_status',
            'status': 'connected'
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'browser_command':
                    await self.handle_browser_command(data, websocket)
                elif message_type == 'vnc_input':
                    # For VNC input, we would forward to VNC server
                    # For now, just acknowledge
                    await websocket.send(json.dumps({
                        'type': 'vnc_input_ack',
                        'success': True
                    }))
                elif message_type == 'screen_request':
                    # Send actual VNC screenshot
                    screen_data = await self.get_vnc_screenshot()
                    await websocket.send(json.dumps({
                        'type': 'vnc_data',
                        'data': screen_data
                    }))
                    
            except json.JSONDecodeError as e:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Invalid JSON: {e}'
                }))
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    'type': 'error', 
                    'message': f'Server error: {e}'
                }))
    

    
    async def handle_browser_command(self, data, websocket):
        """Handle browser control commands"""
        command = data.get('command')
        try:
            if command == 'navigate':
                url = data.get('url', '')
                self.browser_manager.navigate_to(url)
            elif command == 'back':
                self.browser_manager.go_back()
            elif command == 'forward':
                self.browser_manager.go_forward()
            elif command == 'refresh':
                self.browser_manager.refresh()
            elif command == 'new_tab':
                self.browser_manager.new_tab()
            
            await websocket.send(json.dumps({
                'type': 'command_result',
                'success': True,
                'command': command
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'command_result',
                'success': False,
                'command': command,
                'error': str(e)
            }))
    
    async def get_vnc_screenshot(self):
        """Capture screenshot from VNC server"""
        try:
            # Try multiple screenshot methods
            import base64
            
            # Method 1: Try ImageMagick import
            result = subprocess.run([
                'import', '-display', ':1', '-window', 'root', 'png:-'
            ], capture_output=True, timeout=5)
            
            if result.returncode == 0 and len(result.stdout) > 100:
                return base64.b64encode(result.stdout).decode()
            
            # Method 2: Try xwd + convert
            xwd_result = subprocess.run([
                'xwd', '-root', '-display', ':1', '-out', '/tmp/screen.xwd'
            ], capture_output=True, timeout=5)
            
            if xwd_result.returncode == 0:
                convert_result = subprocess.run([
                    'convert', '/tmp/screen.xwd', 'png:-'
                ], capture_output=True, timeout=5)
                
                if convert_result.returncode == 0 and len(convert_result.stdout) > 100:
                    return base64.b64encode(convert_result.stdout).decode()
            
            # Fallback: create a test pattern
            return self.create_test_pattern()
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            # Try to navigate to a default page if browser is not showing anything
            try:
                if hasattr(self, 'browser_manager') and self.browser_manager:
                    self.browser_manager.navigate_to("https://www.example.com")
            except:
                pass
            return self.create_test_pattern()
    
    def create_test_pattern(self):
        """Create a test pattern image using simple SVG to base64"""
        import base64
        try:
            # Create simple SVG test pattern
            svg_content = '''
            <svg width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
                <rect width="1280" height="720" fill="lightblue"/>
                <text x="50" y="100" font-family="Arial" font-size="24" fill="black">VNC Browser - Connecting...</text>
                <rect x="100" y="150" width="400" height="200" fill="none" stroke="black" stroke-width="2"/>
                <text x="120" y="200" font-family="Arial" font-size="18" fill="black">Chromium Browser Window</text>
                <text x="120" y="250" font-family="Arial" font-size="14" fill="gray">Waiting for VNC connection...</text>
            </svg>
            '''
            # Convert SVG to base64
            svg_b64 = base64.b64encode(svg_content.strip().encode('utf-8')).decode()
            return f"data:image/svg+xml;base64,{svg_b64}"
            
        except Exception as e:
            print(f"Error creating test pattern: {e}")
            # Minimal PNG fallback
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def cleanup(self):
        """Clean up resources"""
        self.browser_manager.cleanup()
        self.vnc_server.cleanup()

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)
    
    def log_message(self, format, *args):
        # Suppress HTTP logs
        pass

# Global handler instance  
global_handler = None

async def websocket_handler(websocket):
    """Global WebSocket handler function"""
    global global_handler
    if global_handler:
        await global_handler.handle_client(websocket, websocket.request.path)

async def main():
    global global_handler
    
    # Create VNC WebSocket handler instance for services
    global_handler = VNCWebSocketHandler()
    
    # Start services
    if not await global_handler.start_services():
        print("Failed to start services")
        return
    
    # Start HTTP server for static files (with error handling)
    try:
        http_server = HTTPServer(("0.0.0.0", 5000), HTTPRequestHandler)
        http_thread = threading.Thread(target=http_server.serve_forever)
        http_thread.daemon = True
        http_thread.start()
        print("HTTP server started on http://0.0.0.0:5000")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print("Port 5000 already in use - continuing with existing server")
        else:
            raise e
    
    # Start WebSocket server
    print("Starting WebSocket server on ws://0.0.0.0:8000/ws")
    
    try:
        async with websockets.serve(websocket_handler, "0.0.0.0", 8000):
            print("VNC WebSocket server running...")
            await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if global_handler:
            global_handler.cleanup()
        http_server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
