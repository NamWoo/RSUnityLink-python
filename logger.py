"""
로깅 관리를 위한 싱글톤 클래스
RealSense D435i 데이터 처리와 소켓통신 로그를 관리합니다.
"""

import logging
import logging.handlers
import os
from typing import Optional
from config import Config

class Logger:
    """로깅 관리를 위한 싱글톤 클래스"""
    
    _instance = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._setup_logger()
        self._initialized = True
    
    def _setup_logger(self):
        """로거 설정"""
        config = Config()
        logging_config = config.get_logging_config()
        
        # 로거 생성
        self._logger = logging.getLogger('RSUnityLink')
        self._logger.setLevel(getattr(logging, logging_config['level']))
        
        # 기존 핸들러 제거
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, logging_config['level']))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
        
        # 파일 핸들러 (로테이션)
        if logging_config['file']:
            # 로그 디렉토리 생성
            log_dir = os.path.dirname(logging_config['file'])
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.handlers.RotatingFileHandler(
                logging_config['file'],
                maxBytes=logging_config['max_size'],
                backupCount=logging_config['backup_count']
            )
            file_handler.setLevel(getattr(logging, logging_config['level']))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """로거 인스턴스 반환"""
        return self._logger
    
    def info(self, message: str):
        """정보 로그"""
        self._logger.info(message)
    
    def warning(self, message: str):
        """경고 로그"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """에러 로그"""
        self._logger.error(message)
    
    def debug(self, message: str):
        """디버그 로그"""
        self._logger.debug(message)
    
    def critical(self, message: str):
        """치명적 에러 로그"""
        self._logger.critical(message) 