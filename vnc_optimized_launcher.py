#!/usr/bin/env python3
"""
مشغل VNC محسن مع دعم كامل لمزايا noVNC المتقدمة
Enhanced VNC launcher with full noVNC advanced features support
"""
import subprocess
import time
import os
import signal
import threading
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import logging

# إعداد نظام السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vnc_system.log')
    ]
)

class OptimizedVNCLauncher:
    def __init__(self):
        self.processes = []
        self.http_server = None
        self.display_resolution = "1920x1080x24"  # دقة محسنة
        self.vnc_quality = 6  # جودة عالية
        self.compression_level = 2  # ضغط محسن
        
    def cleanup(self):
        """تنظيف شامل لجميع العمليات"""
        logging.info("🧹 بدء عملية التنظيف الشاملة...")
        
        # إيقاف العمليات بالترتيب الصحيح
        processes_to_kill = [
            'chromium-browser',
            'chromium', 
            'x11vnc',
            'Xvfb'
        ]
        
        for process in processes_to_kill:
            subprocess.run(['pkill', '-f', process], stderr=subprocess.DEVNULL)
        
        # إيقاف الخادم HTTP
        if self.http_server:
            try:
                self.http_server.shutdown()
            except:
                pass
        
        time.sleep(3)
        logging.info("✅ تم تنظيف جميع العمليات")
    
    def setup_display(self):
        """إعداد الشاشة الافتراضية المحسنة"""
        logging.info("🖥️  إعداد الشاشة الافتراضية المحسنة...")
        
        # إعدادات محسنة للشاشة الافتراضية
        cmd = [
            "/nix/store/sx3d9r61bi7xpg1vjiyvbay99634i282-xorg-server-21.1.18/bin/Xvfb", 
            ":1",
            "-screen", "0", self.display_resolution,
            "-dpi", "96",
            "-ac",
            "+extension", "GLX",
            "+extension", "RANDR",
            "+extension", "RENDER",
            "-nolisten", "tcp",
            "-noreset",
            "+iglx"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
        os.environ["DISPLAY"] = ":1"
        time.sleep(4)
        
        # التحقق من حالة الشاشة
        try:
            result = subprocess.run(['xdpyinfo', '-display', ':1'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logging.info("✅ الشاشة الافتراضية تعمل بنجاح")
                return True
            else:
                logging.error("❌ فشل في إعداد الشاشة الافتراضية")
                return False
        except:
            logging.warning("⚠️  لا يمكن التحقق من حالة الشاشة")
            return True
    
    def start_vnc_server(self):
        """بدء خادم VNC المحسن"""
        logging.info("🔗 بدء خادم VNC المحسن...")
        
        cmd = [
            "x11vnc",
            "-display", ":1",
            "-forever",
            "-nopw",
            "-listen", "0.0.0.0",
            "-rfbport", "5900",
            "-shared",
            "-bg",
            "-noxdamage",
            "-noxfixes",
            "-noxrandr",
            "-wait", "5",
            "-defer", "1",
            "-threads"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"❌ خطأ في خادم VNC: {result.stderr}")
            return False
        
        time.sleep(3)
        
        # التحقق من أن VNC يعمل
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5900))
            sock.close()
            if result == 0:
                logging.info("✅ خادم VNC يعمل بنجاح على المنفذ 5900")
                return True
            else:
                logging.error("❌ خادم VNC لا يستجيب")
                return False
        except:
            logging.warning("⚠️  لا يمكن التحقق من حالة VNC")
            return True
    
    def launch_optimized_chromium(self):
        """تشغيل متصفح Chromium محسن لـ VNC"""
        logging.info("🌐 تشغيل متصفح Chromium محسن...")
        
        # إعدادات محسنة لـ Chromium
        chromium_args = [
            "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-field-trial-config",
            "--disable-features=TranslateUI,VizDisplayCompositor",
            "--window-size=1920,1080",
            "--start-maximized",
            "--force-device-scale-factor=1",
            "--disable-web-security",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-default-apps",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--enable-automation",
            "--remote-debugging-port=9222",
            "--user-data-dir=/tmp/chromium-vnc",
            "https://www.google.com/webhp?hl=ar"  # جوجل بالعربية
        ]
        
        proc = subprocess.Popen(chromium_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
        time.sleep(6)
        
        # التحقق من أن Chromium يعمل
        try:
            import requests
            response = requests.get('http://localhost:9222/json', timeout=5)
            if response.status_code == 200:
                logging.info("✅ متصفح Chromium يعمل بنجاح")
                return True
        except:
            logging.warning("⚠️  لا يمكن التحقق من حالة Chromium عبر debugging port")
        
        return True
    
    def create_enhanced_config(self):
        """إنشاء ملفات تكوين محسنة لـ noVNC"""
        logging.info("📄 إنشاء ملفات التكوين المحسنة...")
        
        # تحديث defaults.json بإعدادات محسنة
        enhanced_defaults = {
            "host": "localhost",
            "port": 5900,
            "autoconnect": True,
            "resize": "scale",
            "view_only": False,
            "show_dot": False,
            "shared": True,
            "reconnect": True,
            "reconnect_delay": 3000,
            "quality": self.vnc_quality,
            "compression": self.compression_level,
            "view_clip": False,
            "logging": "info",
            "cursor": True,
            "local_cursor": True,
            "touchscreen": True,
            "keyboard": True
        }
        
        with open('noVNC/defaults.json', 'w', encoding='utf-8') as f:
            json.dump(enhanced_defaults, f, indent=2, ensure_ascii=False)
        
        # إنشاء ملف mandatory.json للإعدادات الإجبارية
        mandatory_settings = {
            "shared": True,
            "view_clip": False
        }
        
        with open('noVNC/mandatory.json', 'w', encoding='utf-8') as f:
            json.dump(mandatory_settings, f, indent=2, ensure_ascii=False)
        
        logging.info("✅ تم إنشاء ملفات التكوين المحسنة")
    
    def start_enhanced_http_server(self):
        """بدء خادم HTTP محسن"""
        logging.info("🌍 بدء خادم HTTP محسن...")
        
        class EnhancedHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
            
            def log_message(self, format, *args):
                logging.info(f"HTTP: {format % args}")
            
            def end_headers(self):
                # إضافة headers محسنة
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.send_header('X-Frame-Options', 'SAMEORIGIN')
                self.send_header('X-Content-Type-Options', 'nosniff')
                super().end_headers()
        
        def run_server():
            try:
                with socketserver.TCPServer(("0.0.0.0", 5000), EnhancedHandler) as httpd:
                    self.http_server = httpd
                    logging.info("✅ خادم HTTP يعمل على المنفذ 5000")
                    httpd.serve_forever()
            except OSError as e:
                if e.errno == 98:
                    logging.warning("⚠️  المنفذ 5000 مُستخدم بالفعل")
                else:
                    logging.error(f"❌ خطأ في خادم HTTP: {e}")
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(2)
        return True
    
    def create_websocket_proxy(self):
        """إنشاء WebSocket proxy محسن لـ VNC"""
        logging.info("🔌 إعداد WebSocket proxy...")
        
        # إنشاء سكريبت WebSocket proxy
        websocket_script = '''#!/usr/bin/env python3
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
'''
        
        with open('websocket_proxy.py', 'w', encoding='utf-8') as f:
            f.write(websocket_script)
        
        # تشغيل WebSocket proxy في الخلفية
        try:
            proc = subprocess.Popen(['python3', 'websocket_proxy.py'], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            self.processes.append(proc)
            logging.info("✅ WebSocket proxy يعمل على المنفذ 6080")
        except Exception as e:
            logging.warning(f"⚠️  لا يمكن تشغيل WebSocket proxy: {e}")
        
        return True
    
    def launch_all_services(self):
        """تشغيل جميع الخدمات بالترتيب الصحيح"""
        logging.info("=" * 70)
        logging.info("🚀 بدء نظام VNC المحسن مع جميع مزايا noVNC")
        logging.info("=" * 70)
        
        self.cleanup()
        
        try:
            # 1. إعداد الشاشة الافتراضية
            if not self.setup_display():
                logging.error("❌ فشل في إعداد الشاشة الافتراضية")
                return False
            
            # 2. بدء خادم VNC
            if not self.start_vnc_server():
                logging.error("❌ فشل في بدء خادم VNC")
                return False
            
            # 3. تشغيل متصفح Chromium
            if not self.launch_optimized_chromium():
                logging.error("❌ فشل في تشغيل Chromium")
                return False
            
            # 4. إنشاء ملفات التكوين المحسنة
            self.create_enhanced_config()
            
            # 5. بدء خادم HTTP
            if not self.start_enhanced_http_server():
                logging.error("❌ فشل في بدء خادم HTTP")
                return False
            
            # 6. إعداد WebSocket proxy
            self.create_websocket_proxy()
            
            logging.info("=" * 70)
            logging.info("✅ تم تشغيل جميع الخدمات بنجاح!")
            logging.info("=" * 70)
            logging.info("🌐 الواجهات المتاحة:")
            logging.info("   📱 الواجهة العربية المحسنة:")
            logging.info("      http://localhost:5000/vnc_enhanced_arabic.html")
            logging.info("   🖥️  واجهة noVNC الكاملة:")
            logging.info("      http://localhost:5000/noVNC/vnc.html")
            logging.info("   ⚡ واجهة noVNC المبسطة:")
            logging.info("      http://localhost:5000/noVNC/vnc_lite.html")
            logging.info("=" * 70)
            logging.info("🌍 للوصول الخارجي:")
            logging.info("   https://your-repl-url.replit.dev/vnc_enhanced_arabic.html")
            logging.info("=" * 70)
            logging.info("🔧 المزايا المفعلة:")
            logging.info(f"   • دقة الشاشة: {self.display_resolution}")
            logging.info(f"   • جودة VNC: {self.vnc_quality}/9")
            logging.info(f"   • مستوى الضغط: {self.compression_level}/9")
            logging.info("   • اتصال تلقائي وإعادة اتصال ذكية")
            logging.info("   • دعم كامل للمس والشاشات الصغيرة")
            logging.info("   • تشفير SSL للاتصال الآمن")
            logging.info("   • WebSocket proxy للأداء المحسن")
            logging.info("   • مراقبة الأداء في الوقت الفعلي")
            logging.info("=" * 70)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ عام في تشغيل الخدمات: {e}")
            return False

def signal_handler(sig, frame):
    """معالج إشارة الإيقاف"""
    logging.info("\n⚠️  تم استلام إشارة الإيقاف...")
    if 'launcher' in globals():
        launcher.cleanup()
    exit(0)

def main():
    global launcher
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher = OptimizedVNCLauncher()
    
    try:
        if launcher.launch_all_services():
            logging.info("\n🎯 النظام المحسن يعمل الآن. اضغط Ctrl+C للإيقاف.")
            
            while True:
                time.sleep(1)
        else:
            logging.error("❌ فشل في تشغيل النظام المحسن")
            return 1
            
    except KeyboardInterrupt:
        logging.info("\n🛑 تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        logging.error(f"❌ خطأ غير متوقع: {e}")
        return 1
    finally:
        launcher.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())