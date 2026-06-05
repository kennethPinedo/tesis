#!/usr/bin/env python3
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORS headers para comunicarse con FastAPI
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_frontend_server(port=5173):
    """Inicia servidor HTTP para el frontend"""
    # Cambiar a directorio dist/
    os.chdir('dist')
    
    server = HTTPServer(('0.0.0.0', port), MyHTTPRequestHandler)
    print(f"\n🚀 Frontend servidor iniciado en http://127.0.0.1:{port}")
    print(f"Sirviendo archivos desde: {os.path.abspath('.')}")
    print(f"\n✓ Backend FastAPI en: http://127.0.0.1:8000")
    print(f"✓ Frontend React en: http://127.0.0.1:{port}")
    print(f"\nPresiona CTRL+C para detener...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Servidor detenido")
        sys.exit(0)

if __name__ == '__main__':
    start_frontend_server(5173)
