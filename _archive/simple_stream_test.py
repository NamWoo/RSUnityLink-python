#!/usr/bin/env python3
"""
컬러 스트림만으로 RealSense 테스트
"""

import pyrealsense2 as rs
import numpy as np
import time

def test_color_only():
    """컬러 스트림만으로 테스트"""
    print("=== 컬러 스트림만 테스트 ===")
    
    try:
        # 1. 컨텍스트 생성
        print("1. 컨텍스트 생성...")
        ctx = rs.context()
        devices = ctx.query_devices()
        print(f"   ✅ 장치: {len(devices)}개")
        
        if len(devices) == 0:
            print("   ❌ 장치 없음")
            return False
        
        # 2. 파이프라인 생성
        print("2. 파이프라인 생성...")
        pipeline = rs.pipeline()
        config = rs.config()
        
        # 3. 컬러 스트림만 설정
        print("3. 컬러 스트림 설정...")
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        print("   ✅ 컬러 스트림 설정 완료")
        
        # 4. 파이프라인 시작
        print("4. 파이프라인 시작...")
        profile = pipeline.start(config)
        print("   ✅ 파이프라인 시작 성공")
        
        # 5. 프레임 받기
        print("5. 프레임 받기...")
        for i in range(5):
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            
            if color_frame:
                print(f"   ✅ 프레임 {i+1}: {color_frame.get_width()}x{color_frame.get_height()}")
            else:
                print(f"   ❌ 프레임 {i+1}: 없음")
        
        # 6. 파이프라인 중지
        print("6. 파이프라인 중지...")
        pipeline.stop()
        print("   ✅ 파이프라인 중지 완료")
        
        print("✅ 컬러 스트림 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

def test_depth_only():
    """뎁스 스트림만으로 테스트"""
    print("\n=== 뎁스 스트림만 테스트 ===")
    
    try:
        # 1. 파이프라인 생성
        print("1. 파이프라인 생성...")
        pipeline = rs.pipeline()
        config = rs.config()
        
        # 2. 뎁스 스트림만 설정
        print("2. 뎁스 스트림 설정...")
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        print("   ✅ 뎁스 스트림 설정 완료")
        
        # 3. 파이프라인 시작
        print("3. 파이프라인 시작...")
        profile = pipeline.start(config)
        print("   ✅ 파이프라인 시작 성공")
        
        # 4. 프레임 받기
        print("4. 프레임 받기...")
        for i in range(5):
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            
            if depth_frame:
                print(f"   ✅ 프레임 {i+1}: {depth_frame.get_width()}x{depth_frame.get_height()}")
            else:
                print(f"   ❌ 프레임 {i+1}: 없음")
        
        # 5. 파이프라인 중지
        print("5. 파이프라인 중지...")
        pipeline.stop()
        print("   ✅ 파이프라인 중지 완료")
        
        print("✅ 뎁스 스트림 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    print("RealSense 개별 스트림 테스트 시작...")
    
    # 컬러 스트림만 테스트
    color_success = test_color_only()
    
    # 잠시 대기
    time.sleep(2)
    
    # 뎁스 스트림만 테스트
    depth_success = test_depth_only()
    
    if color_success and depth_success:
        print("\n✅ 모든 테스트 성공!")
    else:
        print("\n❌ 일부 테스트 실패") 