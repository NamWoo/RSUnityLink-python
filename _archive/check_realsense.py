#!/usr/bin/env python3
"""
RealSense 장치 상태 확인 스크립트
"""

import pyrealsense2 as rs
import sys

def check_realsense():
    """RealSense 장치 상태 확인"""
    print("=== RealSense 장치 상태 확인 ===")
    
    try:
        # RealSense 컨텍스트 생성
        ctx = rs.context()
        
        # 연결된 장치 목록 확인
        devices = ctx.query_devices()
        print(f"발견된 RealSense 장치: {len(devices)}개")
        
        if len(devices) == 0:
            print("❌ RealSense 장치가 연결되지 않았습니다.")
            print("USB 케이블을 확인하고 장치를 다시 연결해보세요.")
            return False
        
        for i, device in enumerate(devices):
            print(f"\n--- 장치 {i+1} ---")
            print(f"이름: {device.get_info(rs.camera_info.name)}")
            print(f"시리얼 번호: {device.get_info(rs.camera_info.serial_number)}")
            print(f"펌웨어 버전: {device.get_info(rs.camera_info.firmware_version)}")
            print(f"USB 타입: {device.get_info(rs.camera_info.usb_type_descriptor)}")
            
            # 센서 정보 확인
            sensors = device.query_sensors()
            print(f"센서 개수: {len(sensors)}")
            
            for j, sensor in enumerate(sensors):
                print(f"  센서 {j+1}: {sensor.get_info(rs.camera_info.name)}")
        
        print("\n✅ RealSense 장치가 정상적으로 연결되어 있습니다.")
        return True
        
    except Exception as e:
        print(f"❌ RealSense 확인 중 오류: {str(e)}")
        return False

def test_streaming():
    """스트리밍 테스트"""
    print("\n=== 스트리밍 테스트 ===")
    
    try:
        # 파이프라인 생성
        pipeline = rs.pipeline()
        config = rs.config()
        
        # 스트림 설정
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        
        print("스트리밍 시작...")
        profile = pipeline.start(config)
        
        print("✅ 스트리밍 시작 성공!")
        
        # 몇 프레임 받기
        for i in range(10):
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if color_frame and depth_frame:
                print(f"프레임 {i+1}: 컬러={color_frame.get_width()}x{color_frame.get_height()}, "
                      f"뎁스={depth_frame.get_width()}x{depth_frame.get_height()}")
        
        pipeline.stop()
        print("✅ 스트리밍 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 스트리밍 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    print("RealSense D435i 상태 확인 중...")
    
    if check_realsense():
        test_streaming()
    else:
        print("\nRealSense 장치를 확인하고 다시 시도해주세요.")
        sys.exit(1) 