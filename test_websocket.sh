#!/bin/bash

# WebSocket 연결 테스트 스크립트
# curl을 사용하여 WebSocket 핸드셰이크 테스트

SERVER_HOST=${1:-"localhost"}
SERVER_PORT=${2:-"8080"}

echo "=== WebSocket 연결 테스트 ==="
echo "서버: $SERVER_HOST:$SERVER_PORT"
echo ""

# 1. HTTP 업그레이드 요청으로 WebSocket 핸드셰이크 테스트
echo "1. WebSocket 핸드셰이크 테스트..."
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
     -H "Sec-WebSocket-Extensions: permessage-deflate" \
     "http://$SERVER_HOST:$SERVER_PORT/"

echo ""
echo "2. 서버 상태 확인 (HTTP GET)..."
curl -s "http://$SERVER_HOST:$SERVER_PORT/" || echo "HTTP 연결 실패 (예상됨 - WebSocket 서버)"

echo ""
echo "3. 포트 연결 테스트..."
nc -zv $SERVER_HOST $SERVER_PORT 2>&1

echo ""
echo "=== 테스트 완료 ==="
echo ""
echo "만약 핸드셰이크가 성공하면 서버가 정상적으로 실행 중입니다."
echo "실제 WebSocket 통신을 테스트하려면 다음을 사용하세요:"
echo "  - 웹 브라우저: websocket_test.html 파일 열기"
echo "  - Python: python3 test_client.py"
echo "  - wscat: wscat -c ws://$SERVER_HOST:$SERVER_PORT" 