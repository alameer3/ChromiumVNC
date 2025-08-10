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
        # Enhanced features
        self.current_resolution = "1280x720"
        self.supported_resolutions = ["1280x720", "1920x1080", "1024x768", "800x600"]
        self.page_loading = False
        self.bookmarks = []
        self.history = []
        self.screenshot_quality = 85  # JPEG quality for faster transfer
        
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
            
            # Send initial tabs info
            tabs_info = self.browser_manager.get_tabs_info()
            await websocket.send(json.dumps({
                'type': 'tabs_updated',
                'tabs': tabs_info,
                'active_tab': self.browser_manager.active_tab_id
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
                # Take browser screenshot with compression
                screenshot = self.browser_manager.driver.get_screenshot_as_base64()
                
                # Get current page info
                current_url = self.browser_manager.driver.current_url
                page_title = self.browser_manager.driver.title
                
                await websocket.send(json.dumps({
                    'type': 'screenshot',
                    'data': screenshot,
                    'format': 'png',
                    'url': current_url,
                    'title': page_title,
                    'resolution': self.current_resolution,
                    'loading': self.page_loading
                }))
                
                # Update history if URL changed
                if current_url and (not self.history or self.history[-1] != current_url):
                    self.history.append(current_url)
                    # Keep only last 50 entries
                    if len(self.history) > 50:
                        self.history = self.history[-50:]
                        
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
                    tab_id = self.browser_manager.new_tab()
                    if tab_id:
                        await websocket.send(json.dumps({
                            'type': 'success',
                            'message': f'New tab opened with ID: {tab_id}'
                        }))
                        # Send updated tabs info
                        tabs_info = self.browser_manager.get_tabs_info()
                        await websocket.send(json.dumps({
                            'type': 'tabs_updated',
                            'tabs': tabs_info,
                            'active_tab': self.browser_manager.active_tab_id
                        }))
                        await asyncio.sleep(1)
                        await self.send_screenshot(websocket)
                elif command == 'close_tab':
                    tab_id = data.get('tab_id')
                    if self.browser_manager.close_tab(tab_id):
                        await websocket.send(json.dumps({
                            'type': 'success',
                            'message': f'Tab {tab_id} closed'
                        }))
                        # Send updated tabs info
                        tabs_info = self.browser_manager.get_tabs_info()
                        await websocket.send(json.dumps({
                            'type': 'tabs_updated',
                            'tabs': tabs_info,
                            'active_tab': self.browser_manager.active_tab_id
                        }))
                        await self.send_screenshot(websocket)
                elif command == 'switch_tab':
                    tab_id = data.get('tab_id')
                    if self.browser_manager.switch_to_tab(tab_id):
                        await websocket.send(json.dumps({
                            'type': 'success',
                            'message': f'Switched to tab {tab_id}'
                        }))
                        # Send updated tabs info
                        tabs_info = self.browser_manager.get_tabs_info()
                        await websocket.send(json.dumps({
                            'type': 'tabs_updated',
                            'tabs': tabs_info,
                            'active_tab': self.browser_manager.active_tab_id
                        }))
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
            
        elif command_type == 'get_bookmarks':
            # Send bookmarks list
            await websocket.send(json.dumps({
                'type': 'bookmarks_list',
                'bookmarks': self.bookmarks
            }))
            
        elif command_type == 'add_bookmark':
            # Add current page to bookmarks
            if self.browser_manager and self.browser_manager.driver:
                try:
                    url = self.browser_manager.driver.current_url
                    title = self.browser_manager.driver.title
                    bookmark = {'url': url, 'title': title}
                    if bookmark not in self.bookmarks:
                        self.bookmarks.append(bookmark)
                        await websocket.send(json.dumps({
                            'type': 'success',
                            'message': 'Bookmark added'
                        }))
                    else:
                        await websocket.send(json.dumps({
                            'type': 'info',
                            'message': 'Page already bookmarked'
                        }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Failed to add bookmark: {e}'
                    }))
                    
        elif command_type == 'get_history':
            # Send browsing history
            await websocket.send(json.dumps({
                'type': 'history_list',
                'history': self.history[-20:]  # Last 20 entries
            }))
            
        elif command_type == 'change_resolution':
            # Change screen resolution
            new_resolution = data.get('resolution')
            if new_resolution in self.supported_resolutions:
                self.current_resolution = new_resolution
                # Update VNC server resolution
                self.vnc_server.screen_resolution = new_resolution
                await websocket.send(json.dumps({
                    'type': 'success',
                    'message': f'Resolution changed to {new_resolution}. Restart required for full effect.'
                }))
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unsupported resolution. Supported: {self.supported_resolutions}'
                }))
                
        elif command_type == 'get_page_info':
            # Get detailed page information
            if self.browser_manager and self.browser_manager.driver:
                try:
                    page_info = {
                        'url': self.browser_manager.driver.current_url,
                        'title': self.browser_manager.driver.title,
                        'loading': self.page_loading,
                        'resolution': self.current_resolution,
                        'history_count': len(self.history),
                        'bookmarks_count': len(self.bookmarks)
                    }
                    await websocket.send(json.dumps({
                        'type': 'page_info',
                        'data': page_info
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Failed to get page info: {e}'
                    }))
    
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