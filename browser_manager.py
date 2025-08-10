"""
Chromium browser management
"""
import subprocess
import os
import signal
import psutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class BrowserManager:
    def __init__(self):
        self.driver = None
        self.display = ":1"
        self.bookmarks = []
        self.history = []
        self.current_resolution = (1280, 720)
        self.tabs = {}  # Store tab information
        self.active_tab_id = 0
        self.next_tab_id = 1
        
    def start_browser(self):
        """Start Chromium browser using Selenium"""
        try:
            # Set display environment
            os.environ["DISPLAY"] = self.display
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280,720")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-data-{os.getpid()}-{int(time.time())}")
            
            # Try to find chromium binary
            import subprocess as sp
            try:
                result = sp.run(['which', 'chromium'], capture_output=True, text=True)
                if result.returncode == 0:
                    chrome_options.binary_location = result.stdout.strip()
                    print(f"Found Chromium at: {chrome_options.binary_location}")
                else:
                    # Try common locations
                    potential_paths = [
                        "/usr/bin/chromium",
                        "/usr/bin/chromium-browser", 
                        "/snap/bin/chromium"
                    ]
                    for path in potential_paths:
                        if os.path.exists(path):
                            chrome_options.binary_location = path
                            print(f"Found Chromium at: {path}")
                            break
                    else:
                        print("Warning: Could not find Chromium binary, using system default")
            except Exception as e:
                print(f"Warning: Could not locate chromium binary: {e}")
            
            # Start Chrome driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to a default page
            self.driver.get("https://www.google.com")
            
            # Initialize first tab
            self.tabs[0] = {
                'id': 0,
                'title': 'Google',
                'url': 'https://www.google.com',
                'window_handle': self.driver.current_window_handle
            }
            
            print("Chromium browser started successfully")
            return True
            
        except Exception as e:
            print(f"Error starting browser: {e}")
            return False
    
    def navigate_to(self, url):
        """Navigate to a specific URL"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.driver.get(url)
            # Add to history
            self.add_to_history(url)
            # Update current tab info
            self.update_current_tab_info()
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return False
    
    def go_back(self):
        """Go back in browser history"""
        try:
            self.driver.back()
            return True
        except Exception as e:
            print(f"Error going back: {e}")
            return False
    
    def go_forward(self):
        """Go forward in browser history"""
        try:
            self.driver.forward()
            return True
        except Exception as e:
            print(f"Error going forward: {e}")
            return False
    
    def refresh(self):
        """Refresh current page"""
        try:
            self.driver.refresh()
            return True
        except Exception as e:
            print(f"Error refreshing: {e}")
            return False
    
    def new_tab(self, url="about:blank"):
        """Open a new tab"""
        try:
            self.driver.execute_script(f"window.open('{url}','_blank');")
            # Switch to the new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Add tab to our tracking
            tab_id = self.next_tab_id
            self.tabs[tab_id] = {
                'id': tab_id,
                'title': 'New Tab',
                'url': url,
                'window_handle': self.driver.current_window_handle
            }
            self.active_tab_id = tab_id
            self.next_tab_id += 1
            
            print(f"New tab opened with ID: {tab_id}")
            return tab_id
        except Exception as e:
            print(f"Error opening new tab: {e}")
            return False
    
    def switch_to_tab(self, tab_id):
        """Switch to a specific tab"""
        try:
            if tab_id in self.tabs:
                self.driver.switch_to.window(self.tabs[tab_id]['window_handle'])
                self.active_tab_id = tab_id
                print(f"Switched to tab {tab_id}")
                return True
            return False
        except Exception as e:
            print(f"Error switching to tab {tab_id}: {e}")
            return False
    
    def close_tab(self, tab_id):
        """Close a specific tab"""
        try:
            if tab_id in self.tabs and len(self.tabs) > 1:
                # Switch to the tab first
                self.driver.switch_to.window(self.tabs[tab_id]['window_handle'])
                self.driver.close()
                
                # Remove from our tracking
                del self.tabs[tab_id]
                
                # Switch to another tab
                if self.active_tab_id == tab_id:
                    # Switch to the first available tab
                    new_active_id = list(self.tabs.keys())[0]
                    self.switch_to_tab(new_active_id)
                
                print(f"Tab {tab_id} closed")
                return True
            return False
        except Exception as e:
            print(f"Error closing tab {tab_id}: {e}")
            return False
    
    def get_tabs_info(self):
        """Get information about all tabs"""
        try:
            current_handle = self.driver.current_window_handle
            tabs_info = []
            
            for tab_id, tab_data in self.tabs.items():
                try:
                    self.driver.switch_to.window(tab_data['window_handle'])
                    tab_data['title'] = self.driver.title or 'Untitled'
                    tab_data['url'] = self.driver.current_url
                    tabs_info.append(tab_data.copy())
                except:
                    # Tab might be closed
                    continue
            
            # Switch back to original tab
            self.driver.switch_to.window(current_handle)
            return tabs_info
        except Exception as e:
            print(f"Error getting tabs info: {e}")
            return []
    
    def update_current_tab_info(self):
        """Update current tab information"""
        try:
            if self.active_tab_id in self.tabs:
                self.tabs[self.active_tab_id]['title'] = self.driver.title or 'Untitled'
                self.tabs[self.active_tab_id]['url'] = self.driver.current_url
        except Exception as e:
            print(f"Error updating tab info: {e}")
    
    def get_current_url(self):
        """Get current URL"""
        try:
            return self.driver.current_url
        except Exception as e:
            print(f"Error getting current URL: {e}")
            return ""
    
    def add_bookmark(self):
        """Add current page to bookmarks"""
        try:
            url = self.get_current_url()
            title = self.driver.title
            if url and url not in [b['url'] for b in self.bookmarks]:
                bookmark = {
                    'title': title,
                    'url': url
                }
                self.bookmarks.append(bookmark)
                print(f"Bookmark added: {title}")
                return True
            return False
        except Exception as e:
            print(f"Error adding bookmark: {e}")
            return False
    
    def get_bookmarks(self):
        """Get all bookmarks"""
        return self.bookmarks
    
    def get_history(self):
        """Get browsing history"""
        return self.history
    
    def add_to_history(self, url):
        """Add URL to history"""
        if url and url not in self.history:
            self.history.append(url)
            # Keep only last 50 entries
            if len(self.history) > 50:
                self.history = self.history[-50:]
    
    def change_resolution(self, width, height):
        """Change browser resolution"""
        try:
            self.current_resolution = (width, height)
            self.driver.set_window_size(width, height)
            print(f"Resolution changed to {width}x{height}")
            return True
        except Exception as e:
            print(f"Error changing resolution: {e}")
            return False
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        # Kill any remaining Chrome processes
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] in ['chrome', 'chromium', 'chromium-browser']:
                    proc.kill()
        except Exception as e:
            print(f"Error cleaning up browser processes: {e}")
        
        print("Browser cleanup completed")
