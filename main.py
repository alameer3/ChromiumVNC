#!/usr/bin/env python3
"""
Main server for web-based Chromium browser with VNC access
"""
import asyncio
import websockets
import json
import subprocess
import os
import signal
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import websockets.server
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
        if path != "/ws":
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
                    # Send a test pattern or actual VNC data
                    await websocket.send(json.dumps({
                        'type': 'vnc_data',
                        'data': 'test_screen_data'
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

async def main():
    # Create VNC WebSocket handler
    handler = VNCWebSocketHandler()
    
    # Start services
    if not await handler.start_services():
        print("Failed to start services")
        return
    
    # Start HTTP server for static files
    http_server = HTTPServer(("0.0.0.0", 5000), HTTPRequestHandler)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.daemon = True
    http_thread.start()
    
    print("HTTP server started on http://0.0.0.0:5000")
    
    # Start WebSocket server
    print("Starting WebSocket server on ws://0.0.0.0:8000/ws")
    
    try:
        async with websockets.serve(handler.handle_client, "0.0.0.0", 8000):
            print("VNC WebSocket server running...")
            await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        handler.cleanup()
        http_server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
