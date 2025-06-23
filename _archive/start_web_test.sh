#!/bin/bash

# RealSense WebSocket 테스트 웹 브라우저 실행 스크립트
# 라즈베리파이에서 HTML 파일을 자동으로 엽니다.

echo "=== RealSense WebSocket 테스트 웹 브라우저 시작 ==="

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_FILE="$SCRIPT_DIR/websocket_test.html"

# HTML 파일 존재 확인
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ websocket_test.html 파일을 찾을 수 없습니다."
    echo "현재 디렉토리: $SCRIPT_DIR"
    exit 1
fi

echo "HTML 파일 경로: $HTML_FILE"

# 라즈베리파이 IP 확인
RASPBERRY_PI_IP=$(hostname -I | awk '{print $1}')
echo "라즈베리파이 IP: $RASPBERRY_PI_IP"

# 웹 브라우저 실행 (여러 옵션 시도)
if command -v chromium-browser &> /dev/null; then
    echo "Chromium 브라우저로 실행 중..."
    chromium-browser --no-sandbox --disable-web-security --user-data-dir=/tmp/chrome_test "$HTML_FILE" &
elif command -v firefox &> /dev/null; then
    echo "Firefox 브라우저로 실행 중..."
    firefox "$HTML_FILE" &
elif command -v google-chrome &> /dev/null; then
    echo "Google Chrome 브라우저로 실행 중..."
    google-chrome --no-sandbox --disable-web-security --user-data-dir=/tmp/chrome_test "$HTML_FILE" &
elif command -v midori &> /dev/null; then
    echo "Midori 브라우저로 실행 중..."
    midori "$HTML_FILE" &
else
    echo "❌ 사용 가능한 웹 브라우저를 찾을 수 없습니다."
    echo "다음 중 하나를 설치하세요:"
    echo "  sudo apt install chromium-browser"
    echo "  sudo apt install firefox"
    echo "  sudo apt install midori"
    exit 1
fi

echo ""
echo "✅ 웹 브라우저가 실행되었습니다!"
echo ""
echo "📋 사용 방법:"
echo "1. 브라우저에서 '연결' 버튼 클릭"
echo "2. 서버 URL 입력: ws://$RASPBERRY_PI_IP:8080"
echo "3. '확인' 클릭"
echo ""
echo "🔧 서버가 실행 중인지 확인:"
echo "  python3 main.py"
echo ""
echo "🌐 외부에서 접속하려면:"
echo "  ws://$RASPBERRY_PI_IP:8080" 