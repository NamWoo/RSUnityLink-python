import socketio
import asyncio
import base64
import cv2
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
from aiohttp import web
app = web.Application()
sio.attach(app)

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    logger.debug(f"Connection environment: {environ}")
    await sio.emit('status', {'message': 'Connected to server'}, to=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def start_streaming(sid, data):
    logger.info(f"Streaming request received from: {sid}")
    logger.debug(f"Streaming request data: {data}")
    # Example: Send 10 dummy frames
    for i in range(10):
        # Create dummy image
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
        logger.debug(f"Sending frame {i+1} to {sid}")
        await sio.emit('frame_data', frame_data, to=sid)
        await asyncio.sleep(0.1)
    logger.info(f"Streaming completed for {sid}")
    await sio.emit('status', {'message': 'Streaming completed'}, to=sid)

@sio.event
async def ping(sid, data):
    logger.debug(f"Ping received from {sid}")
    await sio.emit('pong', {'message': 'pong'}, to=sid)

if __name__ == '__main__':
    logger.info("Starting Socket.IO server on http://0.0.0.0:8080")
    web.run_app(app, host='0.0.0.0', port=8080)