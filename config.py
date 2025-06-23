"""
설정 관리를 위한 싱글톤 클래스
RealSense D435i와 소켓통신 설정을 관리합니다.
"""

import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """설정 관리를 위한 싱글톤 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # --- 기본 설정 파일 경로 ---
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.settings = {}
        self.load_config()
        self._initialized = True
    
    def load_config(self):
        """설정 파일(config.json)을 로드합니다."""
        default_settings = {
            "realsense": {
                # --- 스트림 활성화 설정 ---
                "enable_color": True,
                "enable_depth": True,
                "enable_imu": True,

                # --- 해상도 및 FPS 설정 ---
                # 안정적인 옵션: 424, 240, 15
                # 고해상도 옵션: 640, 480, 30
                "width": 424,
                "height": 240,
                "fps": 15
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.settings = json.load(f)
            else:
                print("config.json 파일이 없어 기본 설정으로 생성합니다.")
                self.settings = default_settings
                self.save_config()
        except Exception as e:
            print(f"설정 로드 실패: {e}. 기본 설정을 사용합니다.")
            self.settings = default_settings

    def save_config(self):
        """현재 설정을 config.json 파일에 저장합니다."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def get_realsense_config(self) -> Dict[str, Any]:
        """RealSense 설정 반환"""
        return self.settings.get('realsense', {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """소켓 설정 반환"""
        return self.settings.get('server', {})
    
    def get_transmission_config(self) -> Dict[str, Any]:
        """전송 설정 반환"""
        return self.settings.get('transmission', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """로깅 설정 반환"""
        return self.settings.get('logging', {}) 