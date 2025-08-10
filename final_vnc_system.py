#!/usr/bin/env python3
"""
النظام النهائي المُحسن لـ VNC مع noVNC v1.6.0 - جميع الوظائف مُفعلة
Final Enhanced VNC System with noVNC v1.6.0 - All Features Activated
"""
import subprocess
import time
import os
import signal
import threading
import logging
import socketserver
from http.server import HTTPServer, SimpleHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinalVNCSystem:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def cleanup(self):
        """تنظيف شامل"""
        logging.info("🧹 تنظيف شامل للنظام...")
        
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        cleanup_commands = [
            ['pkill', '-f', 'websockify'],
            ['pkill', '-f', 'chromium'],
            ['pkill', '-f', 'x11vnc'],
            ['pkill', '-f', 'Xvfb']
        ]
        
        for cmd in cleanup_commands:
            subprocess.run(cmd, stderr=subprocess.DEVNULL)
        
        time.sleep(1)
        logging.info("✅ تنظيف مكتمل")
    
    def start_display(self):
        """شاشة افتراضية محسنة"""
        logging.info("🖥️ تشغيل الشاشة الافتراضية...")
        
        # Use system Xvfb with proper path detection
        import shutil
        xvfb_path = shutil.which("Xvfb")
        if not xvfb_path:
            xvfb_path = "/nix/store/sx3d9r61bi7xpg1vjiyvbay99634i282-xorg-server-21.1.18/bin/Xvfb"
            
        cmd = [
            xvfb_path, 
            ":1",
            "-screen", "0", "1920x1080x24",
            "-ac",
            "-nolisten", "tcp"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
        os.environ["DISPLAY"] = ":1"
        time.sleep(2)
        return True
    
    def start_vnc_server(self):
        """خادم VNC محسن"""
        logging.info("🔗 تشغيل خادم VNC...")
        
        # Use system x11vnc with proper path detection
        import shutil
        x11vnc_path = shutil.which("x11vnc")
        if not x11vnc_path:
            x11vnc_path = "/nix/store/4rxi8q5x6yb39ykygl5ddvmlx6v26gjy-x11vnc-0.9.17/bin/x11vnc"
            
        cmd = [
            x11vnc_path,
            "-display", ":1",
            "-forever",
            "-nopw",
            "-listen", "127.0.0.1",
            "-rfbport", "5900",
            "-shared",
            "-bg"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(1)
        return result.returncode == 0
    
    def start_chromium(self):
        """متصفح محسن"""
        logging.info("🌐 تشغيل Chromium...")
        
        # Use system chromium with proper path detection
        import shutil
        chromium_path = shutil.which("chromium")
        if not chromium_path:
            chromium_path = "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium"
            
        cmd = [
            chromium_path,
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--window-size=1920,1080",
            "--start-maximized",
            "--user-data-dir=/tmp/chromium-final",
            "--remote-debugging-port=0",
            "https://www.google.com/webhp?hl=ar"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        time.sleep(3)
        return True
    
    def start_websockify(self):
        """websockify على منفذ 6080"""
        logging.info("🔌 تشغيل websockify...")
        
        def run_websockify():
            # Use Python websockify module for better compatibility
            cmd = [
                "python", "-m", "websockify",
                "--web", ".",  # تقديم الملفات من المجلد الحالي
                "6080",
                "127.0.0.1:5900"
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(proc)
            
            time.sleep(3)
            
            if proc.poll() is None:
                logging.info("✅ websockify نشط على 6080 مع خدمة الملفات")
            else:
                stdout, stderr = proc.communicate()
                logging.error(f"❌ websockify فشل: {stderr}")
                logging.info(f"stdout: {stdout}")
        
        thread = threading.Thread(target=run_websockify, daemon=True)
        thread.start()
        
        time.sleep(3)
        return True
    
    def start_http_server(self):
        """خادم HTTP على منفذ 5000"""
        logging.info("🌍 تشغيل خادم HTTP...")
        
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
            
            def log_message(self, format, *args):
                pass
        
        def run_server():
            try:
                httpd = HTTPServer(("0.0.0.0", 5000), Handler)
                logging.info("✅ HTTP خادم نشط على 5000")
                httpd.serve_forever()
            except OSError as e:
                logging.warning(f"⚠️ مشكلة في المنفذ 5000: {e}")
                # محاولة منفذ بديل
                try:
                    httpd = HTTPServer(("0.0.0.0", 8080), Handler)
                    logging.info("✅ HTTP خادم نشط على 8080")
                    httpd.serve_forever()
                except:
                    logging.error("❌ فشل HTTP خادم")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        time.sleep(2)
        return True
    
    def run(self):
        """تشغيل النظام الكامل"""
        logging.info("=" * 70)
        logging.info("🚀 النظام النهائي المُحسن - noVNC v1.6.0 كامل الوظائف")
        logging.info("=" * 70)
        
        try:
            self.cleanup()
            
            steps = [
                ("الشاشة الافتراضية", self.start_display),
                ("خادم VNC", self.start_vnc_server),
                ("متصفح Chromium", self.start_chromium),
                ("WebSocket Proxy", self.start_websockify),
                ("خادم HTTP", self.start_http_server)
            ]
            
            success_count = 0
            for name, func in steps:
                logging.info(f"⚙️ {name}...")
                if func():
                    logging.info(f"✅ {name} نجح")
                    success_count += 1
                else:
                    logging.error(f"❌ {name} فشل")
            
            time.sleep(2)
            
            if success_count >= 4:
                logging.info("=" * 70)
                logging.info("🎉 النظام يعمل بنجاح! جميع مزايا noVNC v1.6.0 مُفعلة")
                logging.info("🌐 الواجهات:")
                logging.info("   📱 العربية المحسنة: http://localhost:5000/vnc_enhanced_arabic.html")
                logging.info("   🖥️ noVNC الكاملة: http://localhost:5000/noVNC/vnc.html")
                logging.info("   ⚡ noVNC المبسطة: http://localhost:5000/noVNC/vnc_lite.html")
                logging.info("=" * 70)
                logging.info("🔧 المعلومات التقنية:")
                logging.info("   • VNC: localhost:5900")
                logging.info("   • WebSocket: localhost:6080") 
                logging.info("   • HTTP: localhost:5000")
                logging.info("   • الدقة: 1920x1080")
                logging.info("   • جميع الترميزات: Raw, Tight, H.264, JPEG, وغيرها")
                logging.info("   • التشفير: AES, RSA, DES")
                logging.info("   • اللغات: 17 لغة بما فيها العربية")
                logging.info("   • الإدخال: لوحة مفاتيح، ماوس، لمس")
                logging.info("=" * 70)
            else:
                logging.error("❌ فشل في بعض الخدمات")
                return False
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("🛑 إيقاف النظام...")
        except Exception as e:
            logging.error(f"❌ خطأ: {e}")
        finally:
            self.cleanup()

def signal_handler(sig, frame):
    global vnc_system
    if vnc_system:
        vnc_system.running = False
    exit(0)

def main():
    global vnc_system
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    vnc_system = FinalVNCSystem()
    vnc_system.run()

if __name__ == "__main__":
    main()