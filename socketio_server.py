import socketio
import asyncio
import base64
import cv2
import numpy as np

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
from aiohttp import web
app = web.Application()
sio.attach(app)

@sio.event
async def connect(sid, environ):
    print(f"클라이언트 연결: {sid}")
    await sio.emit('status', {'message': '서버에 연결됨'}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"클라이언트 연결 해제: {sid}")

@sio.event
async def start_streaming(sid, data):
    print(f"스트리밍 시작 요청: {sid}")
    # 예시: 10번 더미 프레임 전송
    for i in range(10):
        # 더미 이미지 생성
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, f"Frame {i+1}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 3)
        _, buffer = cv2.imencode('.jpg', img)
        color_base64 = base64.b64encode(buffer).decode('utf-8')
        frame_data = {
            'color_image': {
                'data': color_base64,
                'width': 640,
                'height': 480,
                'format': 'jpeg'
            },
            'depth_image': None,
            'imu': None
        }
        await sio.emit('frame_data', frame_data, to=sid)
        await asyncio.sleep(0.1)
    await sio.emit('status', {'message': '스트리밍 종료'}, to=sid)

@sio.event
async def ping(sid, data):
    await sio.emit('pong', {'message': 'pong'}, to=sid)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)