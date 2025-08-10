#!/usr/bin/env python3
import asyncio
import websockets
import socket
import threading
import logging

class VNCWebSocketProxy:
    def __init__(self, vnc_host='localhost', vnc_port=5900, ws_port=6080):
        self.vnc_host = vnc_host
        self.vnc_port = vnc_port
        self.ws_port = ws_port
        
    async def vnc_to_ws(self, websocket, vnc_socket):
        try:
            while True:
                data = vnc_socket.recv(4096)
                if not data:
                    break
                await websocket.send(data)
        except Exception as e:
            logging.error(f"VNC to WS error: {e}")
    
    async def ws_to_vnc(self, websocket, vnc_socket):
        try:
            async for message in websocket:
                vnc_socket.send(message)
        except Exception as e:
            logging.error(f"WS to VNC error: {e}")
    
    async def handle_client(self, websocket, path):
        try:
            vnc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            vnc_socket.connect((self.vnc_host, self.vnc_port))
            
            await asyncio.gather(
                self.vnc_to_ws(websocket, vnc_socket),
                self.ws_to_vnc(websocket, vnc_socket)
            )
        except Exception as e:
            logging.error(f"WebSocket proxy error: {e}")
        finally:
            try:
                vnc_socket.close()
            except:
                pass

if __name__ == "__main__":
    proxy = VNCWebSocketProxy()
    start_server = websockets.serve(proxy.handle_client, "0.0.0.0", 6080)
    print("WebSocket proxy running on port 6080")
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
