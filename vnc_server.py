"""
VNC Server management for virtual display
"""
import subprocess
import os
import signal
import time
import psutil

class VNCServer:
    def __init__(self):
        self.xvfb_process = None
        self.vnc_process = None
        self.display = ":1"
        self.vnc_port = 5900
        self.screen_resolution = "1280x720"
        
    def start_xvfb(self):
        """Start Xvfb virtual display"""
        try:
            # Kill any existing Xvfb on this display
            self.cleanup_display()
            
            # Start Xvfb
            cmd = [
                "Xvfb", 
                self.display,
                "-screen", "0", f"{self.screen_resolution}x24",
                "-dpi", "96",
                "-ac",
                "+extension", "GLX",
                "+render"
            ]
            
            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Set DISPLAY environment variable
            os.environ["DISPLAY"] = self.display
            
            print(f"Xvfb started on display {self.display}")
            return True
            
        except Exception as e:
            print(f"Error starting Xvfb: {e}")
            return False
    
    def start_vnc_server(self):
        """Start VNC server"""
        try:
            # Kill any existing VNC server on this port
            self.cleanup_vnc()
            
            # Start x11vnc
            cmd = [
                "x11vnc",
                "-display", self.display,
                "-nopw",  # No password
                "-listen", "0.0.0.0",
                "-xkb",
                "-rfbport", str(self.vnc_port),
                "-shared",
                "-forever",
                "-noxdamage"
            ]
            
            self.vnc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            print(f"VNC server started on port {self.vnc_port}")
            return True
            
        except Exception as e:
            print(f"Error starting VNC server: {e}")
            return False
    
    def cleanup_display(self):
        """Kill existing Xvfb processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'Xvfb':
                    cmdline = proc.info['cmdline'] or []
                    if self.display in cmdline:
                        proc.kill()
                        proc.wait()
        except Exception as e:
            print(f"Error cleaning up display: {e}")
    
    def cleanup_vnc(self):
        """Kill existing VNC processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'x11vnc':
                    cmdline = proc.info['cmdline'] or []
                    if str(self.vnc_port) in ' '.join(cmdline):
                        proc.kill()
                        proc.wait()
        except Exception as e:
            print(f"Error cleaning up VNC: {e}")
    
    def cleanup(self):
        """Clean up VNC server and virtual display"""
        if self.vnc_process:
            try:
                self.vnc_process.terminate()
                self.vnc_process.wait(timeout=5)
            except:
                self.vnc_process.kill()
            
        if self.xvfb_process:
            try:
                self.xvfb_process.terminate()
                self.xvfb_process.wait(timeout=5)
            except:
                self.xvfb_process.kill()
        
        self.cleanup_display()
        self.cleanup_vnc()
        print("VNC server cleanup completed")
    
    def take_screenshot(self):
        """Take screenshot of the VNC display"""
        try:
            import subprocess
            import base64
            
            # Use import command to capture screenshot
            result = subprocess.run([
                'import', '-window', 'root', '-display', self.display, 'png:-'
            ], capture_output=True)
            
            if result.returncode == 0:
                return base64.b64encode(result.stdout).decode('utf-8')
            else:
                print("Screenshot failed:", result.stderr.decode())
                return None
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
    
    def send_mouse_event(self, x, y, buttons):
        """Send mouse event to VNC display"""
        try:
            import subprocess
            
            # Use xdotool to simulate mouse events
            subprocess.run([
                'xdotool', 'mousemove', '--window', 'root', str(x), str(y)
            ], env={'DISPLAY': self.display})
            
            if buttons & 1:  # Left click
                subprocess.run(['xdotool', 'click', '1'], env={'DISPLAY': self.display})
            elif buttons & 4:  # Right click
                subprocess.run(['xdotool', 'click', '3'], env={'DISPLAY': self.display})
            elif buttons & 2:  # Middle click
                subprocess.run(['xdotool', 'click', '2'], env={'DISPLAY': self.display})
                
        except Exception as e:
            print(f"Error sending mouse event: {e}")
    
    def send_key_event(self, key, pressed):
        """Send keyboard event to VNC display"""
        try:
            import subprocess
            
            if pressed:  # Only handle key press, not release
                # Map special keys
                key_map = {
                    'Enter': 'Return',
                    'Backspace': 'BackSpace',
                    'Delete': 'Delete',
                    'Tab': 'Tab',
                    'Escape': 'Escape',
                    'ArrowUp': 'Up',
                    'ArrowDown': 'Down',
                    'ArrowLeft': 'Left',
                    'ArrowRight': 'Right'
                }
                
                mapped_key = key_map.get(key, key)
                subprocess.run(['xdotool', 'key', mapped_key], env={'DISPLAY': self.display})
                
        except Exception as e:
            print(f"Error sending key event: {e}")
