#!/usr/bin/env python3
"""
مشغل VNC محسن مع websockify لتشغيل Chromium في بيئة noVNC
Fixed VNC launcher with websockify for running Chromium in noVNC environment
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FixedVNCLauncher:
    def __init__(self):
        self.processes = []
        self.http_server = None
        self.websockify_process = None
        
    def cleanup(self):
        """تنظيف شامل لجميع العمليات"""
        logging.info("🧹 بدء عملية التنظيف...")
        
        # إيقاف websockify
        if self.websockify_process:
            try:
                self.websockify_process.terminate()
                self.websockify_process.wait(timeout=5)
            except:
                try:
                    self.websockify_process.kill()
                except:
                    pass
        
        # إيقاف العمليات الأخرى
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        # تنظيف بقايا العمليات
        subprocess.run(['pkill', '-f', 'websockify'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'chromium'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'x11vnc'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'Xvfb'], stderr=subprocess.DEVNULL)
        
        time.sleep(2)
        logging.info("✅ تم تنظيف جميع العمليات")
    
    def start_display(self):
        """بدء الشاشة الافتراضية"""
        logging.info("🖥️  بدء الشاشة الافتراضية...")
        
        cmd = [
            "/nix/store/sx3d9r61bi7xpg1vjiyvbay99634i282-xorg-server-21.1.18/bin/Xvfb", 
            ":1",
            "-screen", "0", "1920x1080x24",
            "-dpi", "96",
            "-ac",
            "+extension", "GLX",
            "-nolisten", "tcp"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
        os.environ["DISPLAY"] = ":1"
        time.sleep(3)
        
        logging.info("✅ الشاشة الافتراضية تعمل")
        return True
    
    def start_vnc_server(self):
        """بدء خادم VNC"""
        logging.info("🔗 بدء خادم VNC...")
        
        cmd = [
            "x11vnc",
            "-display", ":1",
            "-forever",
            "-nopw",
            "-listen", "localhost",  # فقط localhost للأمان
            "-rfbport", "5900",
            "-shared",
            "-bg",
            "-noxdamage"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"❌ خطأ في VNC: {result.stderr}")
            return False
        
        time.sleep(2)
        logging.info("✅ خادم VNC يعمل على المنفذ 5900")
        return True
    
    def start_chromium(self):
        """تشغيل متصفح Chromium"""
        logging.info("🌐 تشغيل متصفح Chromium...")
        
        cmd = [
            "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--start-maximized",
            "--force-device-scale-factor=1",
            "--disable-web-security",
            "--disable-extensions",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--user-data-dir=/tmp/chromium-vnc",
            "https://www.google.com/webhp?hl=ar"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
        time.sleep(5)
        logging.info("✅ متصفح Chromium يعمل")
        return True
    
    def start_websockify(self):
        """بدء websockify لتحويل VNC إلى WebSocket"""
        logging.info("🔌 بدء websockify...")
        
        cmd = [
            "/home/runner/workspace/.pythonlibs/bin/websockify",
            "6080",  # منفذ WebSocket
            "localhost:5900"  # عنوان VNC
        ]
        
        self.websockify_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(2)
        
        # التحقق من أن websockify يعمل
        if self.websockify_process.poll() is None:
            logging.info("✅ websockify يعمل على المنفذ 6080")
            return True
        else:
            logging.error("❌ فشل في تشغيل websockify")
            return False
    
    def fix_novnc_config(self):
        """إصلاح تكوين noVNC للعمل مع websockify"""
        logging.info("📄 إصلاح تكوين noVNC...")
        
        # تحديث defaults.json
        defaults = {
            "host": "localhost",
            "port": 6080,  # منفذ websockify
            "autoconnect": True,
            "resize": "scale",
            "view_only": False,
            "shared": True,
            "reconnect": True,
            "reconnect_delay": 3000,
            "path": "websockify"
        }
        
        with open('noVNC/defaults.json', 'w', encoding='utf-8') as f:
            json.dump(defaults, f, indent=2)
        
        # تحديث mandatory.json
        mandatory = {
            "shared": True
        }
        
        with open('noVNC/mandatory.json', 'w', encoding='utf-8') as f:
            json.dump(mandatory, f, indent=2)
        
        logging.info("✅ تم إصلاح تكوين noVNC")
    
    def start_http_server(self):
        """بدء خادم HTTP"""
        logging.info("🌍 بدء خادم HTTP...")
        
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
            
            def log_message(self, format, *args):
                pass  # تعطيل رسائل السجل
        
        def run_server():
            try:
                with socketserver.TCPServer(("0.0.0.0", 5000), Handler) as httpd:
                    self.http_server = httpd
                    httpd.serve_forever()
            except OSError as e:
                if e.errno == 98:
                    logging.warning("⚠️  المنفذ 5000 مُستخدم بالفعل")
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(1)
        logging.info("✅ خادم HTTP يعمل على المنفذ 5000")
        return True
    
    def launch_system(self):
        """تشغيل النظام بالكامل"""
        logging.info("=" * 70)
        logging.info("🚀 بدء نظام VNC المُصحح مع noVNC")
        logging.info("=" * 70)
        
        self.cleanup()
        
        try:
            # 1. بدء الشاشة الافتراضية
            if not self.start_display():
                return False
            
            # 2. بدء خادم VNC
            if not self.start_vnc_server():
                return False
            
            # 3. بدء websockify
            if not self.start_websockify():
                return False
            
            # 4. تشغيل Chromium
            if not self.start_chromium():
                return False
            
            # 5. إصلاح تكوين noVNC
            self.fix_novnc_config()
            
            # 6. بدء خادم HTTP
            if not self.start_http_server():
                return False
            
            logging.info("=" * 70)
            logging.info("✅ جميع الخدمات تعمل بنجاح!")
            logging.info("=" * 70)
            logging.info("🌐 الواجهات المتاحة:")
            logging.info("   📱 الواجهة العربية:")
            logging.info("      http://localhost:5000/vnc_arabic.html")
            logging.info("   🖥️  واجهة noVNC الكاملة:")
            logging.info("      http://localhost:5000/noVNC/vnc.html")
            logging.info("   ⚡ واجهة noVNC المبسطة:")
            logging.info("      http://localhost:5000/noVNC/vnc_lite.html")
            logging.info("=" * 70)
            logging.info("🔧 تفاصيل النظام:")
            logging.info("   • Xvfb على الشاشة :1 (1920x1080)")
            logging.info("   • VNC على localhost:5900")
            logging.info("   • websockify على localhost:6080")
            logging.info("   • HTTP على 0.0.0.0:5000")
            logging.info("   • Chromium مع Google.com بالعربية")
            logging.info("=" * 70)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تشغيل النظام: {e}")
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
    
    launcher = FixedVNCLauncher()
    
    try:
        if launcher.launch_system():
            logging.info("\n🎯 النظام المُصحح يعمل الآن. اضغط Ctrl+C للإيقاف.")
            
            while True:
                time.sleep(1)
        else:
            logging.error("❌ فشل في تشغيل النظام")
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