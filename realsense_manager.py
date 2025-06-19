"""
RealSense D435i 카메라와 IMU 데이터 관리 클래스
비동기로 RealSense 데이터를 처리하고 관리합니다.
"""

import asyncio
import cv2
import numpy as np
import pyrealsense2 as rs
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from logger import Logger
from config import Config

@dataclass
class IMUData:
    """IMU 데이터 구조체"""
    timestamp: float
    gyroscope: Tuple[float, float, float]  # x, y, z (rad/s)
    accelerometer: Tuple[float, float, float]  # x, y, z (m/s²)
    temperature: float

@dataclass
class FrameData:
    """프레임 데이터 구조체"""
    timestamp: float
    color_frame: Optional[np.ndarray]
    depth_frame: Optional[np.ndarray]
    imu_data: Optional[IMUData]

class RealSenseManager:
    """RealSense D435i 관리 싱글톤 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RealSenseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = Logger()
        self.config = Config()
        self.rs_config = self.config.get_realsense_config()
        
        # RealSense 파이프라인
        self.pipeline = None
        self.config_rs = None
        
        # 데이터 저장소
        self.latest_frame_data: Optional[FrameData] = None
        self.latest_imu_data: Optional[IMUData] = None
        
        # 상태 플래그
        self.is_running = False
        self.is_connected = False
        
        # 비동기 태스크
        self._frame_task: Optional[asyncio.Task] = None
        self._imu_task: Optional[asyncio.Task] = None
        
        self._initialized = True
    
    async def initialize(self) -> bool:
        """RealSense 초기화"""
        try:
            self.logger.info("RealSense D435i 초기화 시작...")
            
            # RealSense 컨텍스트 생성
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) == 0:
                self.logger.error("RealSense 장치를 찾을 수 없습니다.")
                return False
            
            self.logger.info(f"발견된 RealSense 장치: {len(devices)}개")
            
            # 장치 정보 출력
            device = devices[0]
            self.logger.info(f"장치 이름: {device.get_info(rs.camera_info.name)}")
            self.logger.info(f"시리얼 번호: {device.get_info(rs.camera_info.serial_number)}")
            self.logger.info(f"펌웨어 버전: {device.get_info(rs.camera_info.firmware_version)}")
            
            # 파이프라인 생성
            self.pipeline = rs.pipeline()
            self.config_rs = rs.config()
            
            # 장치 선택 (시리얼 번호로)
            serial_number = device.get_info(rs.camera_info.serial_number)
            self.config_rs.enable_device(serial_number)
            
            # 스트림 설정 (단순화된 방법)
            try:
                # 기본 해상도로 시작 (더 안정적)
                width = 640
                height = 480
                fps = 30
                
                # 컬러 스트림만 먼저 테스트
                self.config_rs.enable_stream(
                    rs.stream.color,
                    width, height,
                    rs.format.bgr8,
                    fps
                )
                self.logger.info("컬러 스트림 설정 완료")
                
                # 뎁스 스트림 추가
                self.config_rs.enable_stream(
                    rs.stream.depth,
                    width, height,
                    rs.format.z16,
                    fps
                )
                self.logger.info("뎁스 스트림 설정 완료")
                
                # IMU 스트림은 일단 비활성화 (문제가 될 수 있음)
                if self.rs_config['enable_imu']:
                    try:
                        # IMU 스트림은 기본 설정으로
                        self.config_rs.enable_stream(
                            rs.stream.accel,
                            rs.format.motion_xyz32f,
                            250  # IMU는 보통 250Hz
                        )
                        self.config_rs.enable_stream(
                            rs.stream.gyro,
                            rs.format.motion_xyz32f,
                            400  # 자이로는 보통 400Hz
                        )
                        self.logger.info("IMU 스트림 설정 완료")
                    except Exception as e:
                        self.logger.warning(f"IMU 스트림 설정 실패 (무시하고 계속): {str(e)}")
                        self.rs_config['enable_imu'] = False
                
            except Exception as e:
                self.logger.error(f"스트림 설정 실패: {str(e)}")
                return False
            
            # 파이프라인 시작
            try:
                profile = self.pipeline.start(self.config_rs)
                self.logger.info("파이프라인 시작 성공")
            except Exception as e:
                self.logger.error(f"파이프라인 시작 실패: {str(e)}")
                return False
            
            # 스트림 프로파일 정보 가져오기 (선택사항)
            try:
                color_profile = profile.get_stream(rs.stream.color)
                depth_profile = profile.get_stream(rs.stream.depth)
                
                color_intrinsics = color_profile.as_video_stream_profile().get_intrinsics()
                depth_intrinsics = depth_profile.as_video_stream_profile().get_intrinsics()
                
                self.logger.info(f"컬러 스트림 해상도: {color_intrinsics.width}x{color_intrinsics.height}")
                self.logger.info(f"뎁스 스트림 해상도: {depth_intrinsics.width}x{depth_intrinsics.height}")
                
            except Exception as e:
                self.logger.warning(f"스트림 프로파일 정보 가져오기 실패: {str(e)}")
                # 프로파일 정보가 없어도 계속 진행
            
            self.is_connected = True
            self.logger.info("RealSense D435i 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"RealSense 초기화 실패: {str(e)}")
            return False
    
    async def start_streaming(self):
        """스트리밍 시작"""
        if not self.is_connected:
            self.logger.error("RealSense가 연결되지 않았습니다.")
            return
        
        if self.is_running:
            self.logger.warning("이미 스트리밍이 실행 중입니다.")
            return
        
        self.is_running = True
        self.logger.info("RealSense 스트리밍 시작")
        
        # 프레임 처리 태스크 시작
        self._frame_task = asyncio.create_task(self._process_frames())
        
        # IMU 처리 태스크 시작
        if self.rs_config['enable_imu']:
            self._imu_task = asyncio.create_task(self._process_imu())
    
    async def stop_streaming(self):
        """스트리밍 중지"""
        self.is_running = False
        self.logger.info("RealSense 스트리밍 중지")
        
        # 태스크 취소
        if self._frame_task:
            self._frame_task.cancel()
            try:
                await self._frame_task
            except asyncio.CancelledError:
                pass
        
        if self._imu_task:
            self._imu_task.cancel()
            try:
                await self._imu_task
            except asyncio.CancelledError:
                pass
    
    async def _process_frames(self):
        """프레임 처리 비동기 태스크"""
        try:
            while self.is_running:
                # 프레임 대기
                frames = await asyncio.get_event_loop().run_in_executor(
                    None, self.pipeline.wait_for_frames
                )
                
                # 컬러 프레임
                color_frame = frames.get_color_frame()
                color_image = None
                if color_frame:
                    color_image = np.asanyarray(color_frame.get_data())
                
                # 뎁스 프레임
                depth_frame = frames.get_depth_frame()
                depth_image = None
                if depth_frame:
                    depth_image = np.asanyarray(depth_frame.get_data())
                    # 뎁스 이미지를 미터 단위로 변환
                    depth_image = depth_image * self.rs_config['depth_scale']
                
                # 프레임 데이터 생성
                self.latest_frame_data = FrameData(
                    timestamp=datetime.now().timestamp(),
                    color_frame=color_image,
                    depth_frame=depth_image,
                    imu_data=self.latest_imu_data
                )
                
                # 프레임 처리 간격 조절
                await asyncio.sleep(1.0 / self.rs_config['fps'])
                
        except asyncio.CancelledError:
            self.logger.info("프레임 처리 태스크 취소됨")
        except Exception as e:
            self.logger.error(f"프레임 처리 중 오류: {str(e)}")
    
    async def _process_imu(self):
        """IMU 데이터 처리 비동기 태스크"""
        try:
            while self.is_running:
                # IMU 프레임 대기
                frames = await asyncio.get_event_loop().run_in_executor(
                    None, self.pipeline.wait_for_frames
                )
                
                # 자이로스코프 데이터
                gyro_frame = frames.get_gyro_frame()
                gyro_data = None
                if gyro_frame:
                    gyro_data = gyro_frame.get_motion_data()
                
                # 가속도계 데이터
                accel_frame = frames.get_accel_frame()
                accel_data = None
                if accel_frame:
                    accel_data = accel_frame.get_motion_data()
                
                # IMU 데이터 생성
                if gyro_data and accel_data:
                    self.latest_imu_data = IMUData(
                        timestamp=datetime.now().timestamp(),
                        gyroscope=(gyro_data.x, gyro_data.y, gyro_data.z),
                        accelerometer=(accel_data.x, accel_data.y, accel_data.z),
                        temperature=0.0  # D435i는 온도 센서가 없음
                    )
                
                # IMU 처리 간격 조절
                await asyncio.sleep(0.01)  # 100Hz
                
        except asyncio.CancelledError:
            self.logger.info("IMU 처리 태스크 취소됨")
        except Exception as e:
            self.logger.error(f"IMU 처리 중 오류: {str(e)}")
    
    def get_latest_frame_data(self) -> Optional[FrameData]:
        """최신 프레임 데이터 반환"""
        return self.latest_frame_data
    
    def get_latest_imu_data(self) -> Optional[IMUData]:
        """최신 IMU 데이터 반환"""
        return self.latest_imu_data
    
    def get_frame_data_json(self) -> str:
        """프레임 데이터를 JSON 형태로 반환"""
        if not self.latest_frame_data:
            return json.dumps({"error": "데이터가 없습니다."})
        
        data = {
            "timestamp": self.latest_frame_data.timestamp,
            "has_color": self.latest_frame_data.color_frame is not None,
            "has_depth": self.latest_frame_data.depth_frame is not None,
            "has_imu": self.latest_frame_data.imu_data is not None
        }
        
        if self.latest_frame_data.imu_data:
            imu = self.latest_frame_data.imu_data
            data["imu"] = {
                "timestamp": imu.timestamp,
                "gyroscope": imu.gyroscope,
                "accelerometer": imu.accelerometer,
                "temperature": imu.temperature
            }
        
        return json.dumps(data)
    
    async def cleanup(self):
        """리소스 정리"""
        await self.stop_streaming()
        
        if self.pipeline:
            self.pipeline.stop()
            self.pipeline = None
        
        self.is_connected = False
        self.logger.info("RealSense 리소스 정리 완료") 