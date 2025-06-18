#!/bin/bash

# RealSense D435i Unity Link 설치 스크립트
# Raspberry Pi 4용

set -e

echo "=== RealSense D435i Unity Link 설치 시작 ==="

# 시스템 업데이트
echo "시스템 패키지 업데이트 중..."
sudo apt update
sudo apt upgrade -y



# 필수 패키지 설치