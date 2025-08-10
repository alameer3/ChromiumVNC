#!/usr/bin/env python3
"""
Enhanced WebSocket proxy for noVNC with full feature support
وكيل WebSocket محسن لـ noVNC مع دعم جميع الوظائف
"""
import asyncio
import websockets
import socket
import threading
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EnhancedWebSocketProxy:
    def __init__(self, websocket_port=6080, vnc_host='localhost', vnc_port=5900, http_port=5000):
        self.websocket_port = websocket_port
        self.vnc_host = vnc_host
        self.vnc_port = vnc_port
        self.http_port = http_port
        self.clients = set()
        self.vnc_connections = {}
        
    async def vnc_to_websocket(self, websocket, path):
        """ربط VNC بـ WebSocket"""
        logging.info(f"🔗 اتصال WebSocket جديد من {websocket.remote_address}")
        
        try:
            # الاتصال بخادم VNC
            vnc_reader, vnc_writer = await asyncio.open_connection(
                self.vnc_host, self.vnc_port
            )
            
            logging.info(f"✅ تم الاتصال بـ VNC على {self.vnc_host}:{self.vnc_port}")
            
            # إضافة العميل إلى القائمة
            self.clients.add(websocket)
            self.vnc_connections[websocket] = (vnc_reader, vnc_writer)
            
            # إرسال رسالة ترحيب
            await websocket.send(json.dumps({
                'type': 'connection',
                'status': 'connected',
                'message': 'مرحباً بك في نظام VNC المحسن'
            }).encode())
            
            # تشغيل مهام النقل في كلا الاتجاهين
            task1 = asyncio.create_task(self.websocket_to_vnc(websocket, vnc_writer))
            task2 = asyncio.create_task(self.vnc_to_websocket_data(websocket, vnc_reader))
            
            # انتظار إكمال أي من المهام
            done, pending = await asyncio.wait(
                [task1, task2], 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # إلغاء المهام المعلقة
            for task in pending:
                task.cancel()
                
        except Exception as e:
            logging.error(f"❌ خطأ في الاتصال: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'خطأ في الاتصال: {str(e)}'
            }).encode())
        finally:
            # تنظيف الاتصال
            if websocket in self.clients:
                self.clients.remove(websocket)
            if websocket in self.vnc_connections:
                _, vnc_writer = self.vnc_connections[websocket]
                vnc_writer.close()
                await vnc_writer.wait_closed()
                del self.vnc_connections[websocket]
            logging.info("🧹 تم تنظيف الاتصال")
    
    async def websocket_to_vnc(self, websocket, vnc_writer):
        """نقل البيانات من WebSocket إلى VNC"""
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    vnc_writer.write(message)
                    await vnc_writer.drain()
                else:
                    # معالجة رسائل JSON
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'ping':
                            await websocket.send(json.dumps({
                                'type': 'pong',
                                'timestamp': data.get('timestamp')
                            }))
                    except json.JSONDecodeError:
                        pass
        except websockets.exceptions.ConnectionClosed:
            logging.info("🔗 تم إغلاق اتصال WebSocket")
        except Exception as e:
            logging.error(f"❌ خطأ في نقل البيانات إلى VNC: {e}")
    
    async def vnc_to_websocket_data(self, websocket, vnc_reader):
        """نقل البيانات من VNC إلى WebSocket"""
        try:
            while True:
                data = await vnc_reader.read(4096)
                if not data:
                    break
                await websocket.send(data)
        except websockets.exceptions.ConnectionClosed:
            logging.info("🔗 تم إغلاق اتصال WebSocket")
        except Exception as e:
            logging.error(f"❌ خطأ في نقل البيانات من VNC: {e}")
    
    def start_http_server(self):
        """بدء خادم HTTP"""
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)
            
            def log_message(self, format, *args):
                pass  # تعطيل رسائل السجل
            
            def do_GET(self):
                # إضافة headers للأمان وCORS
                if self.path.endswith('.js'):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/javascript')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    with open(self.path[1:], 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    super().do_GET()
        
        try:
            with HTTPServer(("0.0.0.0", self.http_port), Handler) as httpd:
                logging.info(f"🌍 خادم HTTP يعمل على المنفذ {self.http_port}")
                httpd.serve_forever()
        except Exception as e:
            logging.error(f"❌ خطأ في خادم HTTP: {e}")
    
    async def start_websocket_server(self):
        """بدء خادم WebSocket"""
        logging.info(f"🔌 بدء خادم WebSocket على المنفذ {self.websocket_port}")
        
        # تشغيل خادم WebSocket
        server = await websockets.serve(
            self.vnc_to_websocket,
            "0.0.0.0",
            self.websocket_port,
            ping_interval=20,
            ping_timeout=10,
            compression=None  # تعطيل الضغط لتحسين الأداء
        )
        
        logging.info(f"✅ خادم WebSocket جاهز على ws://localhost:{self.websocket_port}")
        
        # مراقبة الإحصائيات
        asyncio.create_task(self.monitor_stats())
        
        await server.wait_closed()
    
    async def monitor_stats(self):
        """مراقبة إحصائيات الاتصال"""
        while True:
            await asyncio.sleep(30)  # كل 30 ثانية
            logging.info(f"📊 العملاء المتصلين: {len(self.clients)}")
            logging.info(f"📊 اتصالات VNC نشطة: {len(self.vnc_connections)}")
    
    def run(self):
        """تشغيل النظام الكامل"""
        logging.info("🚀 بدء النظام المحسن للـ WebSocket Proxy")
        
        # تشغيل خادم HTTP في thread منفصل
        http_thread = threading.Thread(target=self.start_http_server, daemon=True)
        http_thread.start()
        
        # تشغيل خادم WebSocket
        try:
            asyncio.run(self.start_websocket_server())
        except KeyboardInterrupt:
            logging.info("🛑 تم إيقاف النظام")
        except Exception as e:
            logging.error(f"❌ خطأ في النظام: {e}")

def main():
    """الدالة الرئيسية"""
    proxy = EnhancedWebSocketProxy(
        websocket_port=6080,
        vnc_host='localhost',
        vnc_port=5900,
        http_port=5000
    )
    
    proxy.run()

if __name__ == "__main__":
    main()