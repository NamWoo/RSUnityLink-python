"""
RealSense D435i Unity Link 메인 애플리케이션
비동기 소켓 서버를 통해 Unity로 RealSense 데이터를 전송합니다.
"""

import asyncio
import signal
import sys
import os
from typing import Optional
from logger import Logger
from config import Config
from data_transmitter import DataTransmitter

class RSUnityLinkApp:
    """RealSense Unity Link 메인 애플리케이션 클래스"""
    
    def __init__(self):
        self.logger = Logger()
        self.config = Config()
        self.transmitter = DataTransmitter()
        self.is_running = False
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 등)"""
        self.logger.info(f"시그널 {signum} 수신, 애플리케이션 종료 중...")
        self.is_running = False
    
    async def start(self):
        """애플리케이션 시작"""
        try:
            self.logger.info("=== RealSense D435i Unity Link 시작 ===")
            
            # 설정 정보 출력
            socket_config = self.config.get_socket_config()
            rs_config = self.config.get_realsense_config()
            transmission_config = self.config.get_transmission_config()
            
            self.logger.info(f"소켓 서버: {socket_config['host']}:{socket_config['port']}")
            self.logger.info(f"RealSense 해상도: {rs_config['width']}x{rs_config['height']} @ {rs_config['fps']}fps")
            self.logger.info(f"IMU 활성화: {rs_config['enable_imu']}")
            self.logger.info(f"컬러 전송: {transmission_config['enable_color']}")
            self.logger.info(f"뎁스 전송: {transmission_config['enable_depth']}")
            self.logger.info(f"IMU 전송: {transmission_config['enable_imu']}")
            self.logger.info(f"압축 품질: {transmission_config['compression_quality']}%")
            self.logger.info(f"프레임 스킵: {transmission_config['frame_skip']}")
            
            self.is_running = True
            
            # WebSocket 서버 시작
            await self.transmitter.start_server()
            
        except KeyboardInterrupt:
            self.logger.info("키보드 인터럽트로 종료")
        except Exception as e:
            self.logger.error(f"애플리케이션 시작 중 오류: {str(e)}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """리소스 정리"""
        self.logger.info("리소스 정리 중...")
        
        try:
            await self.transmitter.cleanup()
        except Exception as e:
            self.logger.error(f"리소스 정리 중 오류: {str(e)}")
        
        self.logger.info("=== RealSense D435i Unity Link 종료 ===")

async def main():
    """메인 함수"""
    app = RSUnityLinkApp()
    await app.start()

if __name__ == "__main__":
    # Python 3.10 이상 확인
    if sys.version_info < (3, 10):
        print("Python 3.10 이상이 필요합니다.")
        sys.exit(1)
    
    # 현재 디렉토리를 스크립트 디렉토리로 변경
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # 이벤트 루프 실행
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {str(e)}")
        sys.exit(1) 