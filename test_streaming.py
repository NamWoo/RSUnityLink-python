#!/usr/bin/env python3
"""
RealSense 스트리밍 단계별 테스트
"""

import pyrealsense2 as rs
import numpy as np
import time

def test_streaming_step_by_step():
    """단계별 스트리밍 테스트"""
    print("=== RealSense 스트리밍 단계별 테스트 ===")
    
    try:
        # 1. 컨텍스트 생성
        print("1. RealSense 컨텍스트 생성...")
        ctx = rs.context()
        devices = ctx.query_devices()
        print(f"   ✅ 발견된 장치: {len(devices)}개")
        
        if len(devices) == 0:
            print("   ❌ 장치 없음")
            return False
        
        # 2. 장치 정보
        device = devices[0]
        print(f"   장치: {device.get_info(rs.camera_info.name)}")
        print(f"   시리얼: {device.get_info(rs.camera_info.serial_number)}")
        
        # 3. 파이프라인 생성
        print("2. 파이프라인 생성...")
        pipeline = rs.pipeline()
        config = rs.config()
        
        # 4. 장치 선택
        print("3. 장치 선택...")
        serial_number = device.get_info(rs.camera_info.serial_number)
        config.enable_device(serial_number)
        print(f"   ✅ 장치 선택: {serial_number}")
        
        # 5. 컬러 스트림 설정
        print("4. 컬러 스트림 설정...")
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        print("   ✅ 컬러 스트림 설정 완료")
        
        # 6. 뎁스 스트림 설정
        print("5. 뎁스 스트림 설정...")
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        print("   ✅ 뎁스 스트림 설정 완료")
        
        # 7. 파이프라인 시작
        print("6. 파이프라인 시작...")
        profile = pipeline.start(config)
        print("   ✅ 파이프라인 시작 성공")
        
        # 8. 프레임 받기 테스트
        print("7. 프레임 받기 테스트...")
        for i in range(5):
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if color_frame and depth_frame:
                print(f"   ✅ 프레임 {i+1}: 컬러={color_frame.get_width()}x{color_frame.get_height()}, "
                      f"뎁스={depth_frame.get_width()}x{depth_frame.get_height()}")
            else:
                print(f"   ❌ 프레임 {i+1}: 프레임 없음")
        
        # 9. 파이프라인 중지
        print("8. 파이프라인 중지...")
        pipeline.stop()
        print("   ✅ 파이프라인 중지 완료")
        
        print("✅ 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        print(f"오류 타입: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_streaming_step_by_step() 