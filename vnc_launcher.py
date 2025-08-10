#!/usr/bin/env python3
"""
VNC with Chromium launcher - Arabic interface
"""
import subprocess
import time
import os
import signal
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

class VNCLauncher:
    def __init__(self):
        self.processes = []
        self.http_server = None
        
    def cleanup(self):
        """تنظيف جميع العمليات"""
        print("🧹 جاري تنظيف العمليات...")
        subprocess.run(['pkill', '-f', 'Xvfb'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'x11vnc'], stderr=subprocess.DEVNULL) 
        subprocess.run(['pkill', '-f', 'chromium'], stderr=subprocess.DEVNULL)
        time.sleep(2)
    
    def start_xvfb(self):
        """بدء الشاشة الافتراضية"""
        print("🖥️  بدء الشاشة الافتراضية...")
        proc = subprocess.Popen([
            "/nix/store/sx3d9r61bi7xpg1vjiyvbay99634i282-xorg-server-21.1.18/bin/Xvfb", ":1", 
            "-screen", "0", "1280x720x24",
            "-dpi", "96", "-ac", "+extension", "GLX"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.processes.append(proc)
        os.environ["DISPLAY"] = ":1"
        time.sleep(3)
        return True
    
    def start_vnc(self):
        """بدء خادم VNC"""
        print("🔗 بدء خادم VNC...")
        result = subprocess.run([
            "x11vnc", "-display", ":1",
            "-forever", "-nopw", 
            "-listen", "0.0.0.0",
            "-rfbport", "5900",
            "-shared", "-bg", "-noxdamage"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ خطأ في VNC: {result.stderr}")
            return False
            
        time.sleep(2)
        return True
    
    def start_chromium(self):
        """بدء متصفح Chromium"""
        print("🌐 بدء متصفح Chromium...")
        proc = subprocess.Popen([
            "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
            "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--window-size=1280,720", 
            "--start-maximized", "--force-device-scale-factor=1",
            "--disable-web-security", "--disable-extensions",
            "https://www.google.com"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.processes.append(proc)
        time.sleep(5)
        return True
    
    def start_http_server(self):
        """بدء خادم الويب"""
        print("🌍 بدء خادم الويب...")
        
        def run_server():
            class Handler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=".", **kwargs)
                
                def log_message(self, format, *args):
                    pass  # تعطيل رسائل السجل
            
            try:
                with socketserver.TCPServer(("0.0.0.0", 5000), Handler) as httpd:
                    self.http_server = httpd
                    httpd.serve_forever()
            except OSError as e:
                if e.errno == 98:  # Address already in use
                    print("⚠️  المنفذ 5000 مُستخدم بالفعل")
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(2)
        return True
    
    def create_arabic_interface(self):
        """إنشاء واجهة VNC العربية"""
        html_content = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>سطح المكتب البعيد - Chromium VNC</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
            direction: rtl;
        }
        .header {
            background: rgba(0,0,0,0.8);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #4a90e2;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #4a90e2;
        }
        .status {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #00ff00;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
        .vnc-container {
            height: calc(100vh - 70px);
            display: flex;
            justify-content: center;
            align-items: center;
            background: #000;
            position: relative;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: #222;
        }
        .instructions {
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 10px;
            font-size: 14px;
            z-index: 100;
            transition: opacity 0.3s;
        }
        .instructions:hover {
            opacity: 0.5;
        }
        .hide-instructions {
            position: absolute;
            top: 5px;
            left: 5px;
            background: #ff4444;
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🖥️ سطح المكتب البعيد - Chromium</div>
        <div class="status">
            <span>متصل</span>
            <div class="status-dot"></div>
        </div>
    </div>
    
    <div class="vnc-container">
        <div class="instructions" id="instructions">
            <button class="hide-instructions" onclick="document.getElementById('instructions').style.display='none'">✕</button>
            <h3>📋 تعليمات الاستخدام:</h3>
            <ul style="margin-top: 10px; line-height: 1.6;">
                <li>• استخدم الماوس للنقر والتنقل في متصفح Chromium</li>
                <li>• استخدم لوحة المفاتيح للكتابة</li>
                <li>• يمكنك تصفح الإنترنت بشكل كامل</li>
                <li>• للتكبير: Ctrl + عجلة الماوس</li>
                <li>• اضغط على ✕ لإخفاء هذه الرسالة</li>
            </ul>
        </div>
        
        <iframe src="/noVNC/vnc_lite.html?host=''' + f"localhost&port=5900" + '''&autoconnect=true&resize=scale"></iframe>
    </div>
    
    <script>
        console.log('🚀 واجهة VNC العربية تم تحميلها بنجاح');
        
        // إخفاء التعليمات بعد 10 ثواني
        setTimeout(() => {
            const instructions = document.getElementById('instructions');
            if (instructions) {
                instructions.style.opacity = '0.3';
            }
        }, 10000);
    </script>
</body>
</html>'''
        
        with open('vnc_arabic.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("📄 تم إنشاء واجهة VNC العربية: vnc_arabic.html")
    
    def start_all(self):
        """بدء جميع الخدمات"""
        print("=" * 60)
        print("🚀 بدء نظام VNC مع Chromium")
        print("=" * 60)
        
        self.cleanup()
        
        try:
            if not self.start_xvfb():
                return False
                
            if not self.start_vnc():
                return False
                
            if not self.start_chromium():
                return False
            
            self.create_arabic_interface()
                
            if not self.start_http_server():
                return False
            
            print("=" * 60)
            print("✅ تم بدء جميع الخدمات بنجاح!")
            print("=" * 60)
            print("🌐 افتح المتصفح واذهب إلى:")
            print("   http://localhost:5000/vnc_arabic.html")
            print("   أو")
            print("   http://localhost:5000/noVNC/vnc_lite.html?host=localhost&port=5900")
            print("=" * 60)
            print("📱 للوصول من الخارج استخدم:")
            print("   https://your-repl-url.replit.dev/vnc_arabic.html")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في بدء الخدمات: {e}")
            return False

def signal_handler(sig, frame):
    """معالج إشارة الإيقاف"""
    print("\n\n⚠️  تم استلام إشارة الإيقاف...")
    if 'launcher' in globals():
        launcher.cleanup()
    exit(0)

def main():
    global launcher
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher = VNCLauncher()
    
    try:
        if launcher.start_all():
            print("\n🎯 نظام VNC يعمل الآن. اضغط Ctrl+C للإيقاف.")
            
            while True:
                time.sleep(1)
        else:
            print("❌ فشل في بدء خدمات VNC")
            return 1
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return 1
    finally:
        launcher.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())