#!/usr/bin/env python3
"""
نظام VNC بسيط ومحسن مع دعم كامل لـ noVNC
Simple and Enhanced VNC system with full noVNC support
"""
import subprocess
import time
import os
import signal
import threading
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SimpleVNCSystem:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def cleanup(self):
        """تنظيف جميع العمليات"""
        logging.info("🧹 تنظيف النظام...")
        
        # إيقاف العمليات
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        # تنظيف شامل
        subprocess.run(['pkill', '-f', 'websockify'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'chromium'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'x11vnc'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'Xvfb'], stderr=subprocess.DEVNULL)
        
        time.sleep(1)
        logging.info("✅ تم تنظيف النظام")
    
    def start_display(self):
        """بدء الشاشة الافتراضية"""
        logging.info("🖥️ بدء الشاشة الافتراضية...")
        
        cmd = [
            "/nix/store/sx3d9r61bi7xpg1vjiyvbay99634i282-xorg-server-21.1.18/bin/Xvfb", 
            ":1",
            "-screen", "0", "1920x1080x24",
            "-ac"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        
        os.environ["DISPLAY"] = ":1"
        time.sleep(2)
        return True
    
    def start_vnc_server(self):
        """بدء خادم VNC"""
        logging.info("🔗 بدء خادم VNC...")
        
        cmd = [
            "x11vnc",
            "-display", ":1",
            "-forever",
            "-nopw",
            "-listen", "localhost",
            "-rfbport", "5900",
            "-shared",
            "-bg"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(1)
        return result.returncode == 0
    
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
            "--user-data-dir=/tmp/chromium-vnc",
            "https://www.google.com/webhp?hl=ar"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        time.sleep(3)
        return True
    
    def start_websockify_simple(self):
        """تشغيل websockify بطريقة بسيطة"""
        logging.info("🔌 تشغيل websockify...")
        
        def run_websockify():
            cmd = [
                "/home/runner/workspace/.pythonlibs/bin/websockify",
                "6080",
                "localhost:5900"
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processes.append(proc)
            
            # انتظار تشغيل websockify
            time.sleep(2)
            
            if proc.poll() is None:
                logging.info("✅ websockify يعمل على المنفذ 6080")
            else:
                logging.error("❌ فشل websockify")
        
        # تشغيل في thread منفصل
        websock_thread = threading.Thread(target=run_websockify)
        websock_thread.daemon = True
        websock_thread.start()
        
        time.sleep(3)
        return True
    
    def start_http_server(self):
        """بدء خادم HTTP"""
        logging.info("🌍 بدء خادم HTTP...")
        
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
            
            def log_message(self, format, *args):
                pass
        
        def run_server():
            try:
                with socketserver.TCPServer(("0.0.0.0", 5000), Handler) as httpd:
                    logging.info("✅ خادم HTTP يعمل على المنفذ 5000")
                    httpd.serve_forever()
            except OSError as e:
                logging.warning(f"⚠️ خطأ في المنفذ 5000: {e}")
                # محاولة منفذ بديل
                try:
                    with socketserver.TCPServer(("0.0.0.0", 8000), Handler) as httpd:
                        logging.info("✅ خادم HTTP يعمل على المنفذ 8000")
                        httpd.serve_forever()
                except OSError:
                    logging.error("❌ فشل في تشغيل خادم HTTP")
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(1)
        return True
    
    def run(self):
        """تشغيل النظام الكامل"""
        logging.info("=" * 50)
        logging.info("🚀 بدء نظام VNC البسيط والمحسن")
        logging.info("=" * 50)
        
        try:
            self.cleanup()
            
            # تشغيل النظام خطوة بخطوة
            steps = [
                ("الشاشة الافتراضية", self.start_display),
                ("خادم VNC", self.start_vnc_server),
                ("متصفح Chromium", self.start_chromium),
                ("WebSocket Proxy", self.start_websockify_simple),
                ("خادم HTTP", self.start_http_server)
            ]
            
            for step_name, step_func in steps:
                logging.info(f"⚙️ تشغيل {step_name}...")
                if step_func():
                    logging.info(f"✅ {step_name} يعمل")
                else:
                    logging.error(f"❌ فشل في {step_name}")
                    return False
            
            # تأكيد وصول خادم HTTP
            time.sleep(2)
            
            logging.info("=" * 50)
            logging.info("✅ النظام يعمل بنجاح!")
            logging.info("🌐 الواجهات المتاحة:")
            logging.info("   📱 الواجهة العربية المحسنة:")
            logging.info("      http://localhost:5000/vnc_enhanced_arabic.html")
            logging.info("   📱 الواجهة العربية البسيطة:")
            logging.info("      http://localhost:5000/vnc_arabic.html")
            logging.info("   🖥️ واجهة noVNC الكاملة:")
            logging.info("      http://localhost:5000/noVNC/vnc.html")
            logging.info("   ⚡ واجهة noVNC المبسطة:")
            logging.info("      http://localhost:5000/noVNC/vnc_lite.html")
            logging.info("=" * 50)
            logging.info("🔧 تفاصيل تقنية:")
            logging.info("   • VNC Server: localhost:5900")
            logging.info("   • WebSocket Proxy: localhost:6080")
            logging.info("   • HTTP Server: localhost:5000")
            logging.info("   • Display: :1 (1920x1080)")
            logging.info("=" * 50)
            
            # البقاء في التشغيل
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logging.info("🛑 إيقاف النظام...")
        except Exception as e:
            logging.error(f"❌ خطأ: {e}")
        finally:
            self.cleanup()

def signal_handler(sig, frame):
    """معالج إشارة الإيقاف"""
    global vnc_system
    if vnc_system:
        vnc_system.running = False
    exit(0)

def main():
    global vnc_system
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    vnc_system = SimpleVNCSystem()
    vnc_system.run()

if __name__ == "__main__":
    main()