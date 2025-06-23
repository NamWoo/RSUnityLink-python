#!/usr/bin/env python3
"""
최소한의 RealSense 테스트 (Segmentation fault 방지)
"""

import sys
import time

def minimal_test():
    """최소한의 RealSense 테스트"""
    print("=== 최소한의 RealSense 테스트 ===")
    
    try:
        print("1. pyrealsense2 import 시도...")
        import pyrealsense2 as rs
        print("   ✅ pyrealsense2 import 성공")
        
        print("2. 컨텍스트 생성 시도...")
        ctx = rs.context()
        print("   ✅ 컨텍스트 생성 성공")
        
        print("3. 장치 쿼리 시도...")
        devices = ctx.query_devices()
        print(f"   ✅ 장치 쿼리 성공: {len(devices)}개")
        
        if len(devices) > 0:
            device = devices[0]
            print(f"   장치 이름: {device.get_info(rs.camera_info.name)}")
            print(f"   시리얼 번호: {device.get_info(rs.camera_info.serial_number)}")
        
        print("4. 파이프라인 생성 시도...")
        pipeline = rs.pipeline()
        print("   ✅ 파이프라인 생성 성공")
        
        print("5. 설정 생성 시도...")
        config = rs.config()
        print("   ✅ 설정 생성 성공")
        
        print("6. 컬러 스트림 설정 시도...")
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        print("   ✅ 컬러 스트림 설정 성공")
        
        print("7. 파이프라인 시작 시도...")
        profile = pipeline.start(config)
        print("   ✅ 파이프라인 시작 성공")
        
        print("8. 프레임 대기 시도...")
        frames = pipeline.wait_for_frames()
        print("   ✅ 프레임 수신 성공")
        
        print("9. 파이프라인 중지...")
        pipeline.stop()
        print("   ✅ 파이프라인 중지 성공")
        
        print("✅ 모든 테스트 통과!")
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        print(f"오류 타입: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("RealSense 최소 테스트 시작...")
    minimal_test() 