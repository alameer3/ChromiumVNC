#!/usr/bin/env python3
"""
Simple WebSocket server for Chromium VNC browser
"""
import asyncio
import websockets
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from vnc_server import VNCServer
from browser_manager import BrowserManager

class SimpleBrowserServer:
    def __init__(self):
        self.vnc_server = VNCServer()
        self.browser_manager = BrowserManager()
        self.clients = set()
        
    async def start_services(self):
        """Start all backend services"""
        try:
            print("Starting Xvfb...")
            self.vnc_server.start_xvfb()
            await asyncio.sleep(2)
            
            print("Starting VNC server...")
            self.vnc_server.start_vnc_server()
            await asyncio.sleep(2)
            
            print("Starting Chromium...")
            self.browser_manager.start_browser()
            await asyncio.sleep(3)
            
            print("All services ready!")
            return True
        except Exception as e:
            print(f"Error starting services: {e}")
            return False
    
    async def handle_client(self, websocket):
        """Handle WebSocket connections (websockets 15.0.1 format)"""
        self.clients.add(websocket)
        print(f"Client connected from {websocket.remote_address}")
        
        try:
            # Send connection success
            await websocket.send(json.dumps({
                'type': 'status',
                'message': 'Connected to browser'
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.process_command(data, websocket)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid message format'
                    }))
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def send_screenshot(self, websocket):
        """Take a screenshot and send it to the client"""
        try:
            if self.browser_manager and self.browser_manager.driver:
                # Take browser screenshot
                screenshot = self.browser_manager.driver.get_screenshot_as_base64()
                await websocket.send(json.dumps({
                    'type': 'screenshot',
                    'data': screenshot,
                    'format': 'png'
                }))
            else:
                await websocket.send(json.dumps({
                    'type': 'error', 
                    'message': 'Browser not ready for screenshot'
                }))
        except Exception as e:
            print(f"Screenshot error: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Screenshot failed: {str(e)}'
            }))

    async def process_command(self, data, websocket):
        """Process browser commands"""
        command_type = data.get('type')
        
        if command_type == 'browser_command':
            command = data.get('command')
            try:
                if command == 'navigate':
                    url = data.get('url', '')
                    self.browser_manager.navigate_to(url)
                    await websocket.send(json.dumps({
                        'type': 'success',
                        'message': f'Navigating to {url}'
                    }))
                    # Send updated screenshot after navigation
                    await asyncio.sleep(2)  # Wait for page to load
                    await self.send_screenshot(websocket)
                elif command == 'back':
                    self.browser_manager.go_back()
                    await websocket.send(json.dumps({
                        'type': 'success',
                        'message': 'Going back'
                    }))
                    await asyncio.sleep(1)
                    await self.send_screenshot(websocket)
                elif command == 'forward':
                    self.browser_manager.go_forward()
                    await websocket.send(json.dumps({
                        'type': 'success',
                        'message': 'Going forward'
                    }))
                    await asyncio.sleep(1)
                    await self.send_screenshot(websocket)
                elif command == 'refresh':
                    self.browser_manager.refresh()
                    await websocket.send(json.dumps({
                        'type': 'success',
                        'message': 'Refreshing page'
                    }))
                    await asyncio.sleep(2)
                    await self.send_screenshot(websocket)
                elif command == 'new_tab':
                    self.browser_manager.new_tab()
                    await websocket.send(json.dumps({
                        'type': 'success',
                        'message': 'Opening new tab'
                    }))
                    await asyncio.sleep(1)
                    await self.send_screenshot(websocket)
                else:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Unknown command: {command}'
                    }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Command failed: {e}'
                }))
        
        elif command_type == 'ping':
            await websocket.send(json.dumps({
                'type': 'pong',
                'message': 'Server is alive'
            }))
        elif command_type == 'screen_request':
            # Take a screenshot and send it
            await self.send_screenshot(websocket)
    
    def cleanup(self):
        """Clean up all services"""
        self.browser_manager.cleanup()
        self.vnc_server.cleanup()

class HTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

async def main():
    server = SimpleBrowserServer()
    
    # Start backend services
    if not await server.start_services():
        print("Failed to start backend services")
        return
    
    # Start HTTP server for static files
    http_server = HTTPServer(("0.0.0.0", 5000), HTTPHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    print("HTTP server running on port 5000")
    
    # Start WebSocket server  
    print("Starting WebSocket server on port 8000...")
    try:
        async with websockets.serve(server.handle_client, "0.0.0.0", 8000):
            print("WebSocket server running on ws://0.0.0.0:8000/ws")
            print("Browser is ready! Open http://0.0.0.0:5000 in your browser")
            await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        server.cleanup()
        http_server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())