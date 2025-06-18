"""
Unity 클라이언트 테스트를 위한 WebSocket 클라이언트
RealSense D435i 서버에서 전송하는 데이터를 받아서 테스트합니다.
"""

import asyncio
import json
import base64
import cv2
import numpy as np
from datetime import datetime
import websockets
from websockets.client import WebSocketClientProtocol

class TestClient:
    """테스트용 WebSocket 클라이언트"""
    
    def __init__(self, server_url: str = "ws://localhost:8080"):
        self.server_url = server_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.is_connected = False
        self.frame_count = 0
        self.start_time = None
        
    async def connect(self):
        """서버에 연결"""
        try:
            print(f"서버에 연결 중: {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            self.is_connected = True
            self.start_time = datetime.now()
            print("서버에 연결되었습니다.")
            
            # 서버 상태 요청
            await self.send_command("get_status")
            
        except Exception as e:
            print(f"서버 연결 실패: {str(e)}")
            return False
        
        return True
    
    async def disconnect(self):
        """서버 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print("서버 연결이 해제되었습니다.")
    
    async def send_command(self, command: str, **kwargs):
        """서버에 명령 전송"""
        if not self.is_connected:
            print("서버에 연결되지 않았습니다.")
            return
        
        message = {
            "command": command,
            **kwargs
        }
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"명령 전송 실패: {str(e)}")
    
    async def receive_messages(self):
        """서버로부터 메시지 수신"""
        if not self.is_connected:
            return
        
        try:
            async for message in self.websocket:
                await self.process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            print("서버 연결이 끊어졌습니다.")
            self.is_connected = False
        except Exception as e:
            print(f"메시지 수신 중 오류: {str(e)}")
    
    async def process_message(self, message: str):
        """수신된 메시지 처리"""
        try:
            data = json.loads(message)
            message_type = data.get('type', '')
            
            if message_type == 'pong':
                print(f"핑 응답: {data.get('server_time', '')}")
                
            elif message_type == 'status':
                print(f"서버 상태: {data}")
                
            elif message_type == 'success':
                print(f"성공: {data.get('message', '')}")
                
            elif message_type == 'error':
                print(f"오류: {data.get('message', '')}")
                
            elif message_type == 'frame_data':
                await self.process_frame_data(data)
                
            else:
                print(f"알 수 없는 메시지 타입: {message_type}")
                
        except json.JSONDecodeError:
            print("잘못된 JSON 형식")
        except Exception as e:
            print(f"메시지 처리 중 오류: {str(e)}")
    
    async def process_frame_data(self, data: dict):
        """프레임 데이터 처리"""
        self.frame_count += 1
        timestamp = data.get('timestamp', 0)
        
        # 프레임 정보 출력
        if self.frame_count % 30 == 0:  # 30프레임마다 출력
            elapsed = (datetime.now() - self.start_time).total_seconds()
            fps = self.frame_count / elapsed if elapsed > 0 else 0
            print(f"프레임 {self.frame_count}: 타임스탬프={timestamp:.3f}, FPS={fps:.1f}")
        
        # 컬러 이미지 처리
        if 'color_image' in data:
            color_data = data['color_image']
            if color_data.get('data'):
                # Base64 디코딩
                image_data = base64.b64decode(color_data['data'])
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # 이미지 저장 (테스트용)
                if self.frame_count % 100 == 0:  # 100프레임마다 저장
                    cv2.imwrite(f"test_color_{self.frame_count}.jpg", image)
                    print(f"컬러 이미지 저장: test_color_{self.frame_count}.jpg")
        
        # 뎁스 이미지 처리
        if 'depth_image' in data:
            depth_data = data['depth_image']
            if depth_data.get('data'):
                # Base64 디코딩
                image_data = base64.b64decode(depth_data['data'])
                nparr = np.frombuffer(image_data, np.uint8)
                depth_image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                
                # 뎁스 이미지 저장 (테스트용)
                if self.frame_count % 100 == 0:  # 100프레임마다 저장
                    cv2.imwrite(f"test_depth_{self.frame_count}.png", depth_image)
                    print(f"뎁스 이미지 저장: test_depth_{self.frame_count}.png")
        
        # IMU 데이터 처리
        if 'imu' in data:
            imu_data = data['imu']
            if self.frame_count % 30 == 0:  # 30프레임마다 출력
                gyro = imu_data.get('gyroscope', {})
                accel = imu_data.get('accelerometer', {})
                print(f"IMU - 자이로: ({gyro.get('x', 0):.3f}, {gyro.get('y', 0):.3f}, {gyro.get('z', 0):.3f})")
                print(f"IMU - 가속도: ({accel.get('x', 0):.3f}, {accel.get('y', 0):.3f}, {accel.get('z', 0):.3f})")

async def main():
    """메인 함수"""
    client = TestClient()
    
    try:
        # 서버에 연결
        if not await client.connect():
            return
        
        # 스트리밍 시작
        await client.send_command("start_streaming")
        
        # 메시지 수신 시작
        await client.receive_messages()
        
    except KeyboardInterrupt:
        print("\n테스트 클라이언트 종료")
    except Exception as e:
        print(f"테스트 클라이언트 오류: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 