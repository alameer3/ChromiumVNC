#!/usr/bin/env python3
"""
Simple WebSocket to VNC proxy using websockets
"""
import asyncio
import websockets
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class VNCProxy:
    def __init__(self, vnc_host='localhost', vnc_port=5900):
        self.vnc_host = vnc_host
        self.vnc_port = vnc_port
    
    async def vnc_proxy(self, websocket, path):
        """Proxy WebSocket to VNC connection"""
        try:
            # Connect to VNC server
            vnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            vnc_socket.connect((self.vnc_host, self.vnc_port))
            vnc_socket.setblocking(False)
            
            print(f"WebSocket client connected, proxying to VNC {self.vnc_host}:{self.vnc_port}")
            
            async def websocket_to_vnc():
                try:
                    async for message in websocket:
                        if isinstance(message, bytes):
                            vnc_socket.send(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
            
            async def vnc_to_websocket():
                try:
                    while True:
                        try:
                            data = vnc_socket.recv(4096)
                            if not data:
                                break
                            await websocket.send(data)
                        except socket.error:
                            await asyncio.sleep(0.01)
                except websockets.exceptions.ConnectionClosed:
                    pass
            
            # Run both directions concurrently
            await asyncio.gather(
                websocket_to_vnc(),
                vnc_to_websocket(),
                return_exceptions=True
            )
            
        except Exception as e:
            print(f"VNC proxy error: {e}")
        finally:
            try:
                vnc_socket.close()
            except:
                pass
    
    def start_websocket_server(self, port=6080):
        """Start WebSocket server"""
        return websockets.serve(self.vnc_proxy, "0.0.0.0", port)

def start_http_server(port=8080):
    """Start HTTP server for noVNC files"""
    def run_server():
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
        
        with HTTPServer(("0.0.0.0", port), Handler) as httpd:
            print(f"HTTP server started on port {port}")
            httpd.serve_forever()
    
    thread = threading.Thread(target=run_server)
    thread.daemon = True
    thread.start()
    return thread

async def main():
    # Start HTTP server
    http_thread = start_http_server(8080)
    
    # Start VNC proxy
    proxy = VNCProxy()
    websocket_server = await proxy.start_websocket_server(6080)
    print("WebSocket VNC proxy started on port 6080")
    
    # Keep running
    await websocket_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())