import socketio
import asyncio
import base64
import cv2
import numpy as np
import logging
from aiohttp import web
from realsense_manager import RealSenseManager, FrameData

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Socket.IO Server Setup ---
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# --- Global Variables ---
rs_manager = RealSenseManager()
streaming_tasks = {}  # 각 클라이언트(sid)의 스트리밍 작업을 저장

# --- Helper Functions ---
def prepare_frame_data_for_client(frame_data: FrameData):
    """Socket.IO로 전송할 프레임 데이터를 인코딩합니다."""
    if not frame_data:
        logger.warning("prepare_frame_data_for_client: No frame data received.")
        return None

    color_base64 = None
    if frame_data.color_frame is not None:
        ret, buffer = cv2.imencode('.jpg', frame_data.color_frame)
        if ret:
            color_base64 = base64.b64encode(buffer).decode('utf-8')
        else:
            logger.warning("Failed to encode color frame.")

    depth_base64 = None
    if frame_data.depth_frame is not None:
        # Depth data is usually 16-bit, scale it for visualization
        depth_visual = cv2.normalize(frame_data.depth_frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        depth_visual_color = cv2.applyColorMap(depth_visual, cv2.COLORMAP_JET)
        ret, buffer = cv2.imencode('.jpg', depth_visual_color)
        if ret:
            depth_base64 = base64.b64encode(buffer).decode('utf-8')
        else:
            logger.warning("Failed to encode depth frame.")

    imu_payload = None
    if frame_data.imu_data:
        imu = frame_data.imu_data
        imu_payload = {
            'gyroscope': {'x': imu.gyroscope[0], 'y': imu.gyroscope[1], 'z': imu.gyroscope[2]},
            'accelerometer': {'x': imu.accelerometer[0], 'y': imu.accelerometer[1], 'z': imu.accelerometer[2]},
            'temperature': imu.temperature,
        }

    client_data = {
        'color_image': {
            'data': color_base64,
            'width': frame_data.color_frame.shape[1] if color_base64 else 0,
            'height': frame_data.color_frame.shape[0] if color_base64 else 0,
            'format': 'jpeg'
        },
        'depth_image': {
            'data': depth_base64,
            'width': frame_data.depth_frame.shape[1] if depth_base64 else 0,
            'height': frame_data.depth_frame.shape[0] if depth_base64 else 0,
            'format': 'jpeg'
        },
        'imu': imu_payload
    }
    return client_data

async def stream_data_to_client(sid):
    """클라이언트에게 지속적으로 데이터를 전송하는 백그라운드 작업"""
    logger.info(f"Starting data stream for client {sid}")
    while sid in streaming_tasks:
        try:
            latest_frame = rs_manager.get_latest_frame_data()
            if latest_frame:
                client_data = prepare_frame_data_for_client(latest_frame)
                if client_data:
                    await sio.emit('frame_data', client_data, to=sid)
            else:
                logger.debug(f"No new frame data for {sid}, waiting.")
            
            await asyncio.sleep(1.0 / 20.0)  # ~20 FPS
        except asyncio.CancelledError:
            logger.info(f"Streaming task for {sid} was cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in streaming loop for {sid}: {e}", exc_info=True)
            await sio.emit('error', {'message': f"Server streaming error: {e}"}, to=sid)
            break
    logger.info(f"Data stream stopped for client {sid}")

# --- Socket.IO Events ---
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('status', {'message': 'Connected to RealSense Server.'}, to=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    if sid in streaming_tasks:
        streaming_tasks[sid].cancel()
        del streaming_tasks[sid]
        
        if not streaming_tasks: # Stop hardware if no clients are streaming
            logger.info("No active clients. Stopping RealSense streaming.")
            await rs_manager.stop_streaming()

@sio.event
async def start_streaming(sid, data):
    logger.info(f"Received 'start_streaming' request from {sid}")
    if sid in streaming_tasks:
        logger.warning(f"Client {sid} already has a streaming task. Ignoring request.")
        return

    if not rs_manager.is_running:
        logger.info("RealSense manager is not running. Starting it now.")
        await rs_manager.start_streaming()

    task = asyncio.create_task(stream_data_to_client(sid))
    streaming_tasks[sid] = task
    await sio.emit('status', {'message': 'Streaming started.'}, to=sid)

@sio.event
async def stop_streaming(sid, data):
    logger.info(f"Received 'stop_streaming' request from {sid}")
    if sid in streaming_tasks:
        streaming_tasks[sid].cancel()
        del streaming_tasks[sid]
        await sio.emit('status', {'message': 'Streaming stopped.'}, to=sid)
        
        if not streaming_tasks: # Stop hardware if no clients are streaming
            logger.info("No active streams. Stopping RealSense hardware.")
            await rs_manager.stop_streaming()

# --- Main Application Logic ---
async def main():
    logger.info("Initializing RealSense Manager...")
    initialized = await rs_manager.initialize()
    if not initialized:
        logger.error("Failed to initialize RealSense Manager. Exiting.")
        return

    logger.info("Starting Socket.IO server on http://0.0.0.0:8080")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Server is up and running. Waiting for connections.")

    try:
        # Keep the server running until interrupted
        await asyncio.Event().wait()
    finally:
        logger.info("Server is shutting down.")
        await rs_manager.cleanup()
        await runner.cleanup()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user (Ctrl+C).")
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}", exc_info=True)