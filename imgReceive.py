# post 형식으로 이미지와 위치 좌표를 수신한다.
# yolo를 호출하여 결과를 받는다.
# 요청 시작 후 결과나오는 과정에 websocket을 생성하여 연결 유지하며 처리 과정을 클라이언트에게 보낸다.

import http.server
import socketserver
import json
import os
import asyncio
import websockets
import threading
import time
from urllib.parse import parse_qs
from concurrent.futures import ThreadPoolExecutor
from a import prc  # a.py에서 prc 함수를 import

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 전역 변수로 ThreadPoolExecutor 생성
executor = ThreadPoolExecutor(max_workers=5)


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        boundary = self.headers['Content-Type'].split('=')[1].encode()
        parts = post_data.split(boundary)

        filepath = None
        for part in parts:
            if b'filename=' in part:
                filename_start = part.index(b'filename="') + 10
                filename_end = part.index(b'"', filename_start)
                filename = part[filename_start:filename_end].decode()

                content_start = part.index(b'\r\n\r\n') + 4
                content = part[content_start:-2]

                filepath = os.path.join(UPLOAD_FOLDER, filename)
                with open(filepath, 'wb') as f:
                    f.write(content)

            elif b'name="latitude"' in part:
                latitude = part.split(b'\r\n\r\n')[1].strip()

            elif b'name="longitude"' in part:
                longitude = part.split(b'\r\n\r\n')[1].strip()
        print(longitude)
        print(latitude)

        if filepath:
            # prc 함수를 별도의 스레드에서 비동기적으로 실행
            executor.submit(prc, filepath)

        # WebSocket 연결 시작
        self.start_websocket()

        # landing.html 반환
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open('front/landing.html', 'rb') as file:
            self.wfile.write(file.read())

    def start_websocket(self):
        # WebSocket 서버가 아직 실행되지 않았다면 실행
        if not hasattr(self.server, 'websocket_started'):
            websocket_thread = threading.Thread(target=run_websocket_server)
            websocket_thread.daemon = True
            websocket_thread.start()
            self.server.websocket_started = True


def run_http_server():
    with socketserver.TCPServer(("", 8000), RequestHandler) as httpd:
        print("HTTP server running on port 8000")
        httpd.serve_forever()


async def websocket_handler(websocket, path):
    try:
        count = 1
        while True:
            await websocket.send(str(count))
            count = count % 3 + 1
            await asyncio.sleep(3)
    except websockets.exceptions.ConnectionClosed:
        pass


def run_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(websocket_handler, "localhost", 8765)
    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == "__main__":
    run_http_server()
