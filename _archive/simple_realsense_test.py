#!/usr/bin/env python3
"""
간단한 RealSense 테스트
"""

import pyrealsense2 as rs
import sys

def simple_test():
    """간단한 RealSense 테스트"""
    print("=== 간단한 RealSense 테스트 ===")
    
    try:
        # 컨텍스트 생성
        ctx = rs.context()
        print("✅ RealSense 컨텍스트 생성 성공")
        
        # 장치 목록
        devices = ctx.query_devices()
        print(f"✅ 발견된 장치: {len(devices)}개")
        
        if len(devices) > 0:
            device = devices[0]
            print(f"✅ 장치 이름: {device.get_info(rs.camera_info.name)}")
            print(f"✅ 시리얼 번호: {device.get_info(rs.camera_info.serial_number)}")
            
            # 센서 목록
            sensors = device.query_sensors()
            print(f"✅ 센서 개수: {len(sensors)}")
            
            for i, sensor in enumerate(sensors):
                print(f"  센서 {i+1}: {sensor.get_info(rs.camera_info.name)}")
        
        print("✅ 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        print(f"오류 타입: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("RealSense 간단 테스트 시작...")
    simple_test() 