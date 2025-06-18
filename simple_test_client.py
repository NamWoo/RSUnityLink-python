#!/usr/bin/env python3
"""
간단한 WebSocket 연결 테스트 클라이언트
"""

import asyncio
import websockets
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    uri = "ws://localhost:8080"
    
    try:
        logger.info(f"WebSocket 서버에 연결 시도: {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket 연결 성공!")
            
            # 연결 확인 메시지 전송
            test_message = {
                "type": "ping",
                "message": "Hello from test client"
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info(f"메시지 전송: {test_message}")
            
            # 응답 대기 (5초)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"서버 응답: {response}")
            except asyncio.TimeoutError:
                logger.info("서버로부터 응답 없음 (정상 - 데이터 전송만 하는 서버)")
            
            # 3초간 연결 유지
            await asyncio.sleep(3)
            
    except websockets.exceptions.ConnectionRefused:
        logger.error("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        logger.error(f"연결 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection()) 