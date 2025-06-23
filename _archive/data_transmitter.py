"""
Unity로 데이터를 전송하는 비동기 소켓 서버
RealSense D435i의 뎁스 카메라 영상과 IMU 데이터를 Unity로 전송합니다.
"""

import asyncio
import json
import base64
import cv2
import numpy as np
from typing import Set, Optional, Dict, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from logger import Logger
from config import Config
from realsense_manager import RealSenseManager, FrameData
import time

class DataTransmitter:
    """Unity로 데이터를 전송하는 비동기 소켓 서버 싱글톤 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataTransmitter, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = Logger()
        self.config = Config()
        self.socket_config = self.config.get_socket_config()
        self.transmission_config = self.config.get_transmission_config()
        
        # RealSense 매니저
        self.rs_manager = RealSenseManager()
        
        # WebSocket 서버
        self.server = None
        self.clients: Set[WebSocketServerProtocol] = set()
        
        # 상태 플래그
        self.is_running = False
        
        # 비동기 태스크
        self._server_task: Optional[asyncio.Task] = None
        self._transmission_task: Optional[asyncio.Task] = None
        
        self._initialized = True
    
    async def start_server(self):
        """WebSocket 서버 시작"""
        if self.is_running:
            self.logger.warning("서버가 이미 실행 중입니다.")
            return
        
        try:
            self.logger.info(f"WebSocket 서버 시작: {self.socket_config['host']}:{self.socket_config['port']}")
            
            # WebSocket 서버 시작 (함수 정의 방식)
            async def websocket_handler(websocket):
                client_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
                self.logger.info(f"클라이언트 연결: {client_address}")
                
                # 최대 연결 수 확인
                if len(self.clients) >= self.socket_config['max_connections']:
                    self.logger.warning(f"최대 연결 수 초과: {client_address}")
                    await websocket.close(1008, "최대 연결 수 초과")
                    return
                
                # 클라이언트 추가
                self.clients.add(websocket)
                
                try:
                    # 클라이언트와 통신
                    async for message in websocket:
                        await self._process_client_message(websocket, message)
                        
                except websockets.exceptions.ConnectionClosed:
                    self.logger.info(f"클라이언트 연결 종료: {client_address}")
                except Exception as e:
                    self.logger.error(f"클라이언트 처리 중 오류: {str(e)}")
                finally:
                    # 클라이언트 제거
                    self.clients.discard(websocket)
            
            self.server = await websockets.serve(
                websocket_handler,
                self.socket_config['host'],
                self.socket_config['port']
            )
            
            self.is_running = True
            
            # 데이터 전송 태스크 시작
            self._transmission_task = asyncio.create_task(self._transmit_data())
            
            self.logger.info("WebSocket 서버 시작 완료")
            
            # 서버 실행 유지 (종료 시그널 대기)
            try:
                await self.server.wait_closed()
            except asyncio.CancelledError:
                self.logger.info("서버 종료 신호 수신")
                await self.stop_server()
            
        except Exception as e:
            self.logger.error(f"WebSocket 서버 시작 실패: {str(e)}")
            await self.stop_server()
    
    async def stop_server(self):
        """WebSocket 서버 중지"""
        self.is_running = False
        self.logger.info("WebSocket 서버 중지")
        
        # 전송 태스크 취소
        if self._transmission_task:
            self._transmission_task.cancel()
            try:
                await self._transmission_task
            except asyncio.CancelledError:
                pass
        
        # 서버 종료
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # 클라이언트 연결 해제
        for client in self.clients.copy():
            await client.close()
        self.clients.clear()
    
    async def _process_client_message(self, websocket: WebSocketServerProtocol, message: str):
        """클라이언트 메시지 처리"""
        try:
            data = json.loads(message)
            command = data.get('command', '')
            
            if command == 'ping':
                # 핑 응답
                response = {
                    'type': 'pong',
                    'timestamp': datetime.now().timestamp(),
                    'server_time': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
            elif command == 'get_status':
                # 서버 상태 응답
                response = {
                    'type': 'status',
                    'timestamp': datetime.now().timestamp(),
                    'clients_connected': len(self.clients),
                    'realsense_connected': self.rs_manager.is_connected,
                    'realsense_streaming': self.rs_manager.is_running,
                    'transmission_config': self.transmission_config
                }
                await websocket.send(json.dumps(response))
                
            elif command == 'start_streaming':
                # 스트리밍 시작
                if not self.rs_manager.is_connected:
                    success = await self.rs_manager.initialize()
                    if not success:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'RealSense 초기화 실패'
                        }))
                        return
                
                await self.rs_manager.start_streaming()
                await websocket.send(json.dumps({
                    'type': 'success',
                    'message': '스트리밍 시작됨'
                }))
                
            elif command == 'stop_streaming':
                # 스트리밍 중지
                self.logger.info("클라이언트로부터 스트리밍 중지 요청 수신")
                await self.rs_manager.stop_streaming()
                
                # 데이터 전송 태스크도 중지
                if self._transmission_task and not self._transmission_task.done():
                    self._transmission_task.cancel()
                    try:
                        await self._transmission_task
                    except asyncio.CancelledError:
                        pass
                    self.logger.info("데이터 전송 태스크 중지 완료")
                
                await websocket.send(json.dumps({
                    'type': 'success',
                    'message': '스트리밍 중지됨'
                }))
                self.logger.info("RealSense 스트리밍 중지 완료")
                
            else:
                # 알 수 없는 명령
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'알 수 없는 명령: {command}'
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': '잘못된 JSON 형식'
            }))
        except Exception as e:
            self.logger.error(f"클라이언트 메시지 처리 중 오류: {str(e)}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'서버 오류: {str(e)}'
            }))
    
    async def _transmit_data(self):
        """데이터 전송 비동기 태스크"""
        frame_count = 0
        last_transmission_time = time.time()
        
        try:
            while self.is_running:
                # RealSense 스트리밍이 중지된 경우 대기
                if not self.rs_manager.is_running:
                    await asyncio.sleep(0.1)
                    continue
                
                # 프레임 데이터 가져오기
                frame_data = self.rs_manager.get_latest_frame_data()
                if frame_data is None:
                    await asyncio.sleep(0.01)
                    continue
                
                # 프레임 스킵 처리
                frame_count += 1
                if frame_count % self.transmission_config['frame_skip'] != 0:
                    continue
                
                # 전송 데이터 준비
                transmission_data = await self._prepare_transmission_data(frame_data)
                
                # 클라이언트들에게 브로드캐스트
                if self.clients:
                    await self.broadcast_message(transmission_data)
                    
                    # 전송 통계 (1초마다)
                    current_time = time.time()
                    if current_time - last_transmission_time >= 1.0:
                        self.logger.info(f"데이터 전송 중: {len(self.clients)}개 클라이언트, 프레임 {frame_count}")
                        last_transmission_time = current_time
                
                # 프레임 레이트 제어
                await asyncio.sleep(1.0 / 30)  # 30 FPS로 고정
                
        except asyncio.CancelledError:
            self.logger.info("데이터 전송 태스크 취소됨")
        except Exception as e:
            self.logger.error(f"데이터 전송 중 오류: {str(e)}")
    
    async def _prepare_transmission_data(self, frame_data: FrameData) -> Dict[str, Any]:
        """전송 데이터 준비"""
        data = {
            'type': 'frame_data',
            'timestamp': frame_data.timestamp,
            'frame_count': int(frame_data.timestamp * 1000)  # 밀리초 단위
        }
        
        # 컬러 이미지 처리
        if (self.transmission_config['enable_color'] and 
            frame_data.color_frame is not None):
            try:
                # 이미지 압축
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 
                              self.transmission_config['compression_quality']]
                _, buffer = cv2.imencode('.jpg', frame_data.color_frame, encode_param)
                color_base64 = base64.b64encode(buffer).decode('utf-8')
                
                data['color_image'] = {
                    'data': color_base64,
                    'width': frame_data.color_frame.shape[1],
                    'height': frame_data.color_frame.shape[0],
                    'format': 'jpeg'
                }
            except Exception as e:
                self.logger.error(f"컬러 이미지 처리 중 오류: {str(e)}")
        
        # 뎁스 이미지 처리
        if (self.transmission_config['enable_depth'] and 
            frame_data.depth_frame is not None):
            try:
                # 뎁스 이미지를 16비트 PNG로 압축
                depth_normalized = ((frame_data.depth_frame * 1000).astype(np.uint16))
                _, buffer = cv2.imencode('.png', depth_normalized)
                depth_base64 = base64.b64encode(buffer).decode('utf-8')
                
                data['depth_image'] = {
                    'data': depth_base64,
                    'width': frame_data.depth_frame.shape[1],
                    'height': frame_data.depth_frame.shape[0],
                    'format': 'png',
                    'depth_scale': self.rs_manager.rs_config['depth_scale']
                }
            except Exception as e:
                self.logger.error(f"뎁스 이미지 처리 중 오류: {str(e)}")
        
        # IMU 데이터 처리
        if (self.transmission_config['enable_imu'] and 
            frame_data.imu_data is not None):
            imu = frame_data.imu_data
            data['imu'] = {
                'timestamp': imu.timestamp,
                'gyroscope': {
                    'x': imu.gyroscope[0],
                    'y': imu.gyroscope[1],
                    'z': imu.gyroscope[2]
                },
                'accelerometer': {
                    'x': imu.accelerometer[0],
                    'y': imu.accelerometer[1],
                    'z': imu.accelerometer[2]
                },
                'temperature': imu.temperature
            }
        
        return data
    
    def get_client_count(self) -> int:
        """연결된 클라이언트 수 반환"""
        return len(self.clients)
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """모든 클라이언트에게 메시지 브로드캐스트"""
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"브로드캐스트 중 오류: {str(e)}")
                disconnected_clients.add(client)
        
        # 연결이 끊어진 클라이언트 제거
        for client in disconnected_clients:
            self.clients.discard(client)
    
    async def cleanup(self):
        """리소스 정리"""
        await self.stop_server()
        await self.rs_manager.cleanup()
        self.logger.info("DataTransmitter 리소스 정리 완료") 