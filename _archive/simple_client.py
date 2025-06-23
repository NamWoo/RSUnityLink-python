#!/usr/bin/env python3
"""
간단한 RealSense WebSocket 클라이언트
외부에서 서버에 연결하여 테스트합니다.
"""

import asyncio
import json
import websockets
import sys

async def test_connection(server_url):
    """서버에 연결하여 테스트"""
    print(f"서버에 연결 중: {server_url}")
    
    try:
        async with websockets.connect(server_url) as websocket:
            print("✅ 연결 성공!")
            
            # 핑 테스트
            print("\n1. 핑 테스트...")
            await websocket.send(json.dumps({"command": "ping"}))
            response = await websocket.recv()
            print(f"핑 응답: {response}")
            
            # 상태 확인
            print("\n2. 서버 상태 확인...")
            await websocket.send(json.dumps({"command": "get_status"}))
            response = await websocket.recv()
            status_data = json.loads(response)
            print(f"서버 상태: {json.dumps(status_data, indent=2)}")
            
            # 스트리밍 시작
            print("\n3. 스트리밍 시작...")
            await websocket.send(json.dumps({"command": "start_streaming"}))
            response = await websocket.recv()
            print(f"스트리밍 시작 응답: {response}")
            
            # 데이터 수신 (10초간)
            print("\n4. 데이터 수신 테스트 (10초간)...")
            frame_count = 0
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data.get('type') == 'frame_data':
                        frame_count += 1
                        if frame_count % 5 == 0:  # 5프레임마다 출력
                            print(f"프레임 {frame_count} 수신됨")
                    
                except asyncio.TimeoutError:
                    print("데이터 수신 타임아웃")
                    break
            
            print(f"총 {frame_count}개 프레임 수신됨")
            
            # 스트리밍 중지
            print("\n5. 스트리밍 중지...")
            await websocket.send(json.dumps({"command": "stop_streaming"}))
            response = await websocket.recv()
            print(f"스트리밍 중지 응답: {response}")
            
            print("\n✅ 테스트 완료!")
            
    except websockets.exceptions.InvalidURI:
        print("❌ 잘못된 WebSocket URL입니다.")
        print("올바른 형식: ws://IP:PORT")
    except websockets.exceptions.ConnectionRefused:
        print("❌ 연결이 거부되었습니다.")
        print("서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 연결 오류: {e}")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        server_url = input("서버 URL을 입력하세요 (예: ws://192.168.45.236:8080): ")
    
    if not server_url.startswith(('ws://', 'wss://')):
        server_url = f"ws://{server_url}"
    
    print("=== RealSense WebSocket 클라이언트 테스트 ===")
    asyncio.run(test_connection(server_url))

if __name__ == "__main__":
    main() 