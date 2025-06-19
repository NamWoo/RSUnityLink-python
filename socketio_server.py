import socketio
import asyncio
import base64
import cv2
import numpy as np
import logging
import math

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
    
    # Example: Send 10 dummy frames with actual values
    for i in range(10):
        # Create dummy image with frame number and timestamp
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add a moving pattern to make it more visible
        for y in range(480):
            for x in range(640):
                img[y,x] = [(x + i * 20) % 255, (y + i * 20) % 255, (x + y + i * 20) % 255]
                
        cv2.putText(img, f"Frame {i+1}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 3)
        _, buffer = cv2.imencode('.jpg', img)
        color_base64 = base64.b64encode(buffer).decode('utf-8')

        # Create dummy depth image
        depth_img = np.zeros((480, 640), dtype=np.uint16)
        # Add a distance pattern
        for y in range(480):
            for x in range(640):
                depth_img[y,x] = ((x + y + i * 50) % 1000) + 500  # Values between 500-1500mm
        
        # Convert depth to visualization
        depth_viz = cv2.normalize(depth_img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        _, depth_buffer = cv2.imencode('.jpg', depth_viz)
        depth_base64 = base64.b64encode(depth_buffer).decode('utf-8')

        # Generate some moving IMU data
        time_factor = i * 0.1
        frame_data = {
            'color_image': {
                'data': color_base64,
                'width': 640,
                'height': 480,
                'format': 'jpeg'
            },
            'depth_image': {
                'data': depth_base64,
                'width': 640,
                'height': 480,
                'format': 'jpeg'
            },
            'imu': {
                'gyroscope': {
                    'x': math.sin(time_factor) * 10.0,
                    'y': math.cos(time_factor) * 10.0,
                    'z': math.sin(time_factor * 2) * 5.0
                },
                'accelerometer': {
                    'x': math.sin(time_factor) * 9.81,
                    'y': math.cos(time_factor) * 9.81,
                    'z': 9.81
                },
                'temperature': 25.0 + math.sin(time_factor) * 2.0
            }
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