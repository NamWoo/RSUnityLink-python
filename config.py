"""
설정 관리를 위한 싱글톤 클래스
RealSense D435i와 소켓통신 설정을 관리합니다.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """설정 관리를 위한 싱글톤 클래스"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # .env 파일 로드
        load_dotenv()
        
        # RealSense 설정
        self.realsense_config = {
            'width': int(os.getenv('REALSENSE_WIDTH', '640')),
            'height': int(os.getenv('REALSENSE_HEIGHT', '480')),
            'fps': int(os.getenv('REALSENSE_FPS', '30')),
            'depth_scale': float(os.getenv('RS_DEPTH_SCALE', 0.001)),
            'enable_imu': os.getenv('REALSENSE_ENABLE_IMU', 'False').lower() == 'true'
        }
        
        # 소켓 서버 설정
        self.socket_config = {
            'host': os.getenv('SOCKET_HOST', '0.0.0.0'),
            'port': int(os.getenv('SOCKET_PORT', 8080)),
            'max_connections': int(os.getenv('MAX_CONNECTIONS', 5))
        }
        
        # 데이터 전송 설정
        self.transmission_config = {
            'enable_color': os.getenv('ENABLE_COLOR', 'True').lower() == 'true',
            'enable_depth': os.getenv('ENABLE_DEPTH', 'False').lower() == 'true',
            'enable_imu': os.getenv('ENABLE_IMU', 'False').lower() == 'true',
            'compression_quality': int(os.getenv('COMPRESSION_QUALITY', '80')),
            'frame_skip': int(os.getenv('FRAME_SKIP', '1'))
        }
        
        # 로깅 설정
        self.logging_config = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': os.getenv('LOG_FILE', 'rs_unity_link.log'),
            'max_size': int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024)),  # 10MB
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5))
        }
        
        self._initialized = True
    
    def get_realsense_config(self) -> Dict[str, Any]:
        """RealSense 설정 반환"""
        return self.realsense_config.copy()
    
    def get_socket_config(self) -> Dict[str, Any]:
        """소켓 설정 반환"""
        return self.socket_config.copy()
    
    def get_transmission_config(self) -> Dict[str, Any]:
        """전송 설정 반환"""
        return self.transmission_config.copy()
    
    def get_logging_config(self) -> Dict[str, Any]:
        """로깅 설정 반환"""
        return self.logging_config.copy() 