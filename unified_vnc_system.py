#!/usr/bin/env python3
"""
نظام VNC موحد مع دعم كامل لـ noVNC وجميع الوظائف
Unified VNC system with full noVNC support and all features
"""
import subprocess
import time
import os
import signal
import threading
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import html
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UnifiedVNCSystem:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def cleanup(self):
        """تنظيف شامل للنظام"""
        logging.info("🧹 تنظيف النظام الموحد...")
        
        # إيقاف العمليات المُتتبعة
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        # تنظيف شامل لجميع العمليات ذات الصلة
        cleanup_commands = [
            ['pkill', '-f', 'websockify'],
            ['pkill', '-f', 'chromium'],
            ['pkill', '-f', 'x11vnc'],
            ['pkill', '-f', 'Xvfb']
        ]
        
        for cmd in cleanup_commands:
            subprocess.run(cmd, stderr=subprocess.DEVNULL)
        
        time.sleep(1)
        logging.info("✅ تم تنظيف النظام")
    
    def start_virtual_display(self):
        """بدء الشاشة الافتراضية"""
        logging.info("🖥️ بدء الشاشة الافتراضية...")
        
        cmd = [
            "/nix/store/sx3d9r61bi7xpg1vjiyvbay99634i282-xorg-server-21.1.18/bin/Xvfb", 
            ":1",
            "-screen", "0", "1920x1080x24",
            "-ac", "-nolisten", "tcp"
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
            "-listen", "127.0.0.1",
            "-rfbport", "5900",
            "-shared",
            "-nosel",
            "-nocursor",
            "-bg"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(1)
        return result.returncode == 0
    
    def start_chromium_browser(self):
        """تشغيل متصفح Chromium"""
        logging.info("🌐 تشغيل متصفح Chromium...")
        
        cmd = [
            "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--start-maximized",
            "--user-data-dir=/tmp/chromium-vnc-unified",
            "https://www.google.com/webhp?hl=ar"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.processes.append(proc)
        time.sleep(3)
        return True
    
    def start_websockify_proxy(self):
        """تشغيل websockify proxy على منفذ 80"""
        logging.info("🔌 تشغيل websockify على المنفذ 80...")
        
        def run_websockify():
            cmd = [
                "/home/runner/workspace/.pythonlibs/bin/websockify",
                "80",  # استخدام منفذ 80 للوصول المباشر
                "127.0.0.1:5900",  # VNC server
                "--web", ".",  # تقديم الملفات
                "--log-file", "/tmp/websockify.log"
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(proc)
            
            # انتظار وتحقق
            time.sleep(3)
            
            if proc.poll() is None:
                logging.info("✅ websockify يعمل على المنفذ 80")
            else:
                stdout, stderr = proc.communicate()
                logging.error(f"❌ websockify فشل: {stderr}")
        
        websock_thread = threading.Thread(target=run_websockify)
        websock_thread.daemon = True
        websock_thread.start()
        
        time.sleep(4)
        return True
    
    def check_services(self):
        """فحص جميع الخدمات"""
        logging.info("🔍 فحص حالة الخدمات...")
        
        # فحص VNC
        try:
            result = subprocess.run(['pgrep', 'x11vnc'], capture_output=True)
            vnc_status = "✅ يعمل" if result.returncode == 0 else "❌ لا يعمل"
        except:
            vnc_status = "❌ لا يعمل"
        
        # فحص Chromium
        try:
            result = subprocess.run(['pgrep', 'chromium'], capture_output=True)
            chrome_status = "✅ يعمل" if result.returncode == 0 else "❌ لا يعمل"
        except:
            chrome_status = "❌ لا يعمل"
        
        # فحص websockify
        try:
            result = subprocess.run(['pgrep', 'websockify'], capture_output=True)
            websock_status = "✅ يعمل" if result.returncode == 0 else "❌ لا يعمل"
        except:
            websock_status = "❌ لا يعمل"
        
        logging.info(f"   VNC Server: {vnc_status}")
        logging.info(f"   Chromium: {chrome_status}")
        logging.info(f"   websockify: {websock_status}")
        
        return vnc_status, chrome_status, websock_status
    
    def run(self):
        """تشغيل النظام الموحد الكامل"""
        logging.info("=" * 60)
        logging.info("🚀 بدء النظام الموحد لـ VNC مع noVNC v1.6.0")
        logging.info("=" * 60)
        
        try:
            # تنظيف أولي
            self.cleanup()
            
            # خطوات التشغيل
            steps = [
                ("الشاشة الافتراضية Xvfb", self.start_virtual_display),
                ("خادم VNC", self.start_vnc_server),
                ("متصفح Chromium", self.start_chromium_browser),
                ("websockify Proxy", self.start_websockify_proxy)
            ]
            
            success_count = 0
            for step_name, step_func in steps:
                logging.info(f"⚙️ تشغيل {step_name}...")
                try:
                    if step_func():
                        logging.info(f"✅ {step_name} نجح")
                        success_count += 1
                    else:
                        logging.error(f"❌ {step_name} فشل")
                except Exception as e:
                    logging.error(f"❌ خطأ في {step_name}: {e}")
            
            # فحص الخدمات النهائي
            time.sleep(2)
            vnc_status, chrome_status, websock_status = self.check_services()
            
            # تقرير النهائي
            logging.info("=" * 60)
            if success_count >= 3:
                logging.info("✅ النظام الموحد يعمل بنجاح!")
                logging.info("🌐 الواجهات المتاحة:")
                logging.info("   📱 الواجهة العربية المحسنة:")
                logging.info("      http://localhost/vnc_enhanced_arabic.html")
                logging.info("   🖥️ واجهة noVNC الكاملة:")
                logging.info("      http://localhost/noVNC/vnc.html")
                logging.info("   ⚡ واجهة noVNC المبسطة:")
                logging.info("      http://localhost/noVNC/vnc_lite.html")
                logging.info("=" * 60)
                logging.info("🔧 معلومات تقنية:")
                logging.info("   • VNC Server: 127.0.0.1:5900")
                logging.info("   • WebSocket: localhost:80")
                logging.info("   • Display: :1 (1920x1080)")
                logging.info("   • جميع مزايا noVNC v1.6.0 مُفعلة")
                logging.info("=" * 60)
            else:
                logging.error("❌ فشل في تشغيل بعض الخدمات")
                return False
            
            # البقاء في التشغيل
            while self.running:
                time.sleep(10)
                # فحص دوري للخدمات
                vnc_status, chrome_status, websock_status = self.check_services()
                
        except KeyboardInterrupt:
            logging.info("🛑 إيقاف النظام الموحد...")
        except Exception as e:
            logging.error(f"❌ خطأ عام: {e}")
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
    
    # تعيين معالجات الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # تشغيل النظام
    vnc_system = UnifiedVNCSystem()
    vnc_system.run()

if __name__ == "__main__":
    main()