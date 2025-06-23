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
import logging
from config import Config

logger = logging.getLogger(__name__)

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
            logger.info("RealSense D435i 초기화 시작...")
            
            # --- 설정 로드 ---
            cfg = self.rs_config
            enable_color = cfg.get('enable_color', True)
            enable_depth = cfg.get('enable_depth', True)
            enable_imu = cfg.get('enable_imu', True)
            width = cfg.get('width', 424)
            height = cfg.get('height', 240)
            fps = cfg.get('fps', 15)
            
            logger.info(f"설정: Color={enable_color}, Depth={enable_depth}, IMU={enable_imu}, {width}x{height}@{fps}fps")

            # RealSense 컨텍스트 생성
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) == 0:
                logger.error("RealSense 장치를 찾을 수 없습니다.")
                return False
            
            logger.info(f"발견된 RealSense 장치: {len(devices)}개")
            
            # 장치 정보 출력
            device = devices[0]
            logger.info(f"장치 이름: {device.get_info(rs.camera_info.name)}")
            logger.info(f"시리얼 번호: {device.get_info(rs.camera_info.serial_number)}")
            logger.info(f"펌웨어 버전: {device.get_info(rs.camera_info.firmware_version)}")
            
            # 파이프라인 생성
            self.pipeline = rs.pipeline()
            self.config_rs = rs.config()
            
            # 장치 선택 (시리얼 번호로)
            serial_number = device.get_info(rs.camera_info.serial_number)
            self.config_rs.enable_device(serial_number)
            
            # 스트림 설정 (설정에 따라 조건부로 활성화)
            try:
                if not enable_color and not enable_depth and not enable_imu:
                    logger.error("모든 스트림이 비활성화되어 있습니다. 하나 이상을 활성화해야 합니다.")
                    return False
                
                if enable_color:
                    self.config_rs.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
                    logger.info("컬러 스트림 설정 완료")

                if enable_depth:
                    self.config_rs.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
                    logger.info("뎁스 스트림 설정 완료")
                
                if enable_imu:
                    try:
                        self.config_rs.enable_stream(rs.stream.accel)
                        self.config_rs.enable_stream(rs.stream.gyro)
                        logger.info("IMU (Accel, Gyro) 스트림 설정 완료")
                    except Exception as e:
                        logger.warning(f"IMU 스트림 설정 실패 (하드웨어 미지원 가능): {e}")
                        cfg['enable_imu'] = False # 실패 시 설정도 비활성화

            except Exception as e:
                logger.error(f"스트림 설정 중 오류 발생: {str(e)}", exc_info=True)
                return False
            
            # 파이프라인 시작 (가장 안정적인 방법으로 변경)
            # 라이브러리가 하드웨어에 가장 적합한 설정을 자동으로 찾도록 rs.config() 객체를 전달하지 않음
            try:
                profile = self.pipeline.start()
                logger.info("파이프라인 시작 성공 (자동 설정)")
            except Exception as e:
                logger.error(f"파이프라인 시작 실패: {str(e)}", exc_info=True)
                return False
            
            # 스트림 프로파일 정보 가져오기 (선택사항)
            try:
                color_profile = profile.get_stream(rs.stream.color)
                depth_profile = profile.get_stream(rs.stream.depth)
                
                color_intrinsics = color_profile.as_video_stream_profile().get_intrinsics()
                depth_intrinsics = depth_profile.as_video_stream_profile().get_intrinsics()
                
                logger.info(f"컬러 스트림 해상도: {color_intrinsics.width}x{color_intrinsics.height}")
                logger.info(f"뎁스 스트림 해상도: {depth_intrinsics.width}x{depth_intrinsics.height}")
                
                # 해상도가 다르면 경고
                if color_intrinsics.width != depth_intrinsics.width or color_intrinsics.height != depth_intrinsics.height:
                    logger.warning("컬러와 뎁스 해상도가 다릅니다!")
                    logger.warning(f"컬러: {color_intrinsics.width}x{color_intrinsics.height}")
                    logger.warning(f"뎁스: {depth_intrinsics.width}x{depth_intrinsics.height}")
                
            except Exception as e:
                logger.warning(f"스트림 프로파일 정보 가져오기 실패: {str(e)}")
                # 프로파일 정보가 없어도 계속 진행
            
            self.is_connected = True
            logger.info("RealSense D435i 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"RealSense 초기화 실패: {str(e)}", exc_info=True)
            return False
    
    async def start_streaming(self):
        """스트리밍 시작"""
        if not self.is_connected:
            logger.error("RealSense가 연결되지 않았습니다.")
            return
        
        if self.is_running:
            logger.warning("이미 스트리밍이 실행 중입니다.")
            return
        
        self.is_running = True
        logger.info("RealSense 스트리밍 시작")
        
        # 프레임 처리 태스크 시작
        self._frame_task = asyncio.create_task(self._process_all_frames())
    
    async def stop_streaming(self):
        """스트리밍 중지"""
        if not self.is_running:
            logger.warning("이미 스트리밍이 중지되어 있습니다.")
            return
        
        logger.info("RealSense 스트리밍 중지 시작")
        self.is_running = False
        
        # 태스크 취소
        if self._frame_task:
            self._frame_task.cancel()
            try:
                await self._frame_task
            except asyncio.CancelledError:
                pass
            self._frame_task = None
        
        if self._imu_task:
            self._imu_task.cancel()
            try:
                await self._imu_task
            except asyncio.CancelledError:
                pass
            self._imu_task = None
        
        # 파이프라인 중지
        if self.pipeline:
            try:
                # 파이프라인이 실행 중인지 확인
                if hasattr(self.pipeline, '_running') and self.pipeline._running:
                    self.pipeline.stop()
                    logger.info("RealSense 파이프라인 중지 완료")
                else:
                    logger.info("파이프라인이 이미 중지되어 있음")
            except Exception as e:
                logger.error(f"파이프라인 중지 중 오류: {str(e)}")
        
        logger.info("RealSense 스트리밍 중지 완료")
    
    async def _process_all_frames(self):
        """(통합) 프레임 및 IMU 데이터 처리 비동기 태스크"""
        try:
            while self.is_running:
                frames = await asyncio.get_event_loop().run_in_executor(
                    None, self.pipeline.wait_for_frames
                )

                # --- 이미지 프레임 처리 ---
                color_frame = frames.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data()) if color_frame else None

                depth_frame = frames.get_depth_frame()
                depth_image = np.asanyarray(depth_frame.get_data()) if depth_frame else None
                
                # --- IMU 프레임 처리 ---
                if self.rs_config.get('enable_imu', False):
                    gyro_frame = frames.first_or_default(rs.stream.gyro)
                    accel_frame = frames.first_or_default(rs.stream.accel)

                    if gyro_frame and accel_frame:
                        gyro_data = gyro_frame.as_motion_frame().get_motion_data()
                        accel_data = accel_frame.as_motion_frame().get_motion_data()
                        
                        self.latest_imu_data = IMUData(
                            timestamp=gyro_frame.get_timestamp(),
                            gyroscope=(gyro_data.x, gyro_data.y, gyro_data.z),
                            accelerometer=(accel_data.x, accel_data.y, accel_data.z),
                            temperature=0.0  # D435i IMU는 온도 센서 미포함
                        )

                # --- 최종 데이터 객체 생성 ---
                self.latest_frame_data = FrameData(
                    timestamp=datetime.now().timestamp(),
                    color_frame=color_image,
                    depth_frame=depth_image,
                    imu_data=self.latest_imu_data # 가장 최근의 IMU 데이터를 첨부
                )
                
                # 프레임 처리 간격 조절
                await asyncio.sleep(1.0 / self.rs_config.get('fps', 15))
                
        except asyncio.CancelledError:
            logger.info("프레임 처리 태스크 취소됨")
        except Exception as e:
            logger.error(f"프레임 처리 중 오류: {str(e)}", exc_info=True)
    
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
        logger.info("RealSense 리소스 정리 완료") 