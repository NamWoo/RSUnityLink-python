# RealSense D435i Unity Link - Python

RealSense D435i 카메라에서 뎁스 카메라 영상과 IMU 데이터를 비동기 소켓통신으로 Unity에 전송하는 Python 애플리케이션입니다.

## 주요 기능

- **RealSense D435i 지원**: 뎁스 카메라와 IMU 데이터 동시 처리
- **비동기 처리**: asyncio를 사용한 고성능 비동기 처리
- **싱글톤 패턴**: 메모리 효율적인 싱글톤 클래스 구조
- **WebSocket 서버**: Unity와의 실시간 통신
- **설정 관리**: 환경 변수를 통한 유연한 설정
- **로깅 시스템**: 상세한 로그 기록 및 로테이션

## 시스템 요구사항

- **Python**: 3.10 이상
- **OS**: Linux (Raspberry Pi 4 권장)
- **하드웨어**: Intel RealSense D435i 카메라
- **네트워크**: WebSocket 통신 지원

## 설치 방법

### 1. 저장소 클론
```bash
git clone <repository-url>
cd RSUnityLink-python
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 설정
```bash
# 환경 변수 파일 복사
cp env_example.txt .env

# 필요에 따라 .env 파일 편집
nano .env
```

## 설정 옵션

### RealSense 설정
- `RS_WIDTH`: 컬러/뎁스 스트림 너비 (기본값: 640)
- `RS_HEIGHT`: 컬러/뎁스 스트림 높이 (기본값: 480)
- `RS_FPS`: 프레임 레이트 (기본값: 30)
- `RS_DEPTH_SCALE`: 뎁스 스케일 (기본값: 0.001)
- `RS_ENABLE_IMU`: IMU 활성화 (기본값: true)

### 소켓 서버 설정
- `SOCKET_HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `SOCKET_PORT`: 서버 포트 (기본값: 8080)
- `MAX_CONNECTIONS`: 최대 연결 수 (기본값: 5)

### 데이터 전송 설정
- `ENABLE_DEPTH`: 뎁스 이미지 전송 (기본값: true)
- `ENABLE_COLOR`: 컬러 이미지 전송 (기본값: true)
- `ENABLE_IMU`: IMU 데이터 전송 (기본값: true)
- `COMPRESSION_QUALITY`: 이미지 압축 품질 (기본값: 80)
- `FRAME_SKIP`: 프레임 스킵 (기본값: 1)

### 로깅 설정
- `LOG_LEVEL`: 로그 레벨 (기본값: INFO)
- `LOG_FILE`: 로그 파일 경로 (기본값: logs/rs_unity_link.log)
- `LOG_MAX_SIZE`: 로그 파일 최대 크기 (기본값: 10MB)
- `LOG_BACKUP_COUNT`: 로그 백업 파일 수 (기본값: 5)

## 사용 방법

### 1. 서버 실행
```bash
python main.py
```

### 2. 테스트 클라이언트 실행
```bash
python test_client.py
```

## 프로젝트 구조

```
RSUnityLink-python/
├── main.py                 # 메인 애플리케이션 진입점
├── config.py              # 설정 관리 싱글톤 클래스
├── logger.py              # 로깅 관리 싱글톤 클래스
├── realsense_manager.py   # RealSense D435i 관리 클래스
├── data_transmitter.py    # WebSocket 서버 및 데이터 전송
├── test_client.py         # 테스트용 WebSocket 클라이언트
├── requirements.txt       # Python 의존성 패키지
├── env_example.txt        # 환경 변수 설정 예제
└── README.md             # 프로젝트 문서
```

## 클래스 구조

### Config (싱글톤)
- 환경 변수 기반 설정 관리
- RealSense, 소켓, 전송, 로깅 설정 제공

### Logger (싱글톤)
- 콘솔 및 파일 로깅
- 로그 로테이션 지원
- 다양한 로그 레벨 지원

### RealSenseManager (싱글톤)
- RealSense D435i 초기화 및 관리
- 비동기 프레임 및 IMU 데이터 처리
- 데이터 구조체 정의 (FrameData, IMUData)

### DataTransmitter (싱글톤)
- WebSocket 서버 관리
- 클라이언트 연결 처리
- 데이터 압축 및 전송

## 데이터 형식

### 프레임 데이터
```json
{
  "type": "frame_data",
  "timestamp": 1234567890.123,
  "frame_count": 1234567890123,
  "color_image": {
    "data": "base64_encoded_jpeg",
    "width": 640,
    "height": 480,
    "format": "jpeg"
  },
  "depth_image": {
    "data": "base64_encoded_png",
    "width": 640,
    "height": 480,
    "format": "png",
    "depth_scale": 0.001
  },
  "imu": {
    "timestamp": 1234567890.123,
    "gyroscope": {
      "x": 0.1,
      "y": 0.2,
      "z": 0.3
    },
    "accelerometer": {
      "x": 9.8,
      "y": 0.1,
      "z": 0.2
    },
    "temperature": 25.0
  }
}
```

### 클라이언트 명령
```json
{
  "command": "start_streaming"
}
```

### 서버 응답
```json
{
  "type": "success",
  "message": "스트리밍 시작됨"
}
```

## Unity 연동

Unity에서는 WebSocket 클라이언트를 구현하여 이 서버에 연결하고 데이터를 수신할 수 있습니다.

### Unity WebSocket 클라이언트 예제
```csharp
using WebSocketSharp;
using Newtonsoft.Json;

public class RealSenseClient : MonoBehaviour
{
    private WebSocket webSocket;
    
    void Start()
    {
        webSocket = new WebSocket("ws://raspberry-pi-ip:8080");
        webSocket.OnMessage += OnMessage;
        webSocket.Connect();
    }
    
    void OnMessage(object sender, MessageEventArgs e)
    {
        var data = JsonConvert.DeserializeObject<FrameData>(e.Data);
        // 데이터 처리
    }
}
```

## 문제 해결

### RealSense 장치를 찾을 수 없는 경우
1. RealSense D435i가 올바르게 연결되었는지 확인
2. USB 권한 확인: `sudo usermod -a -G video $USER`
3. RealSense SDK 설치 확인

### WebSocket 연결 실패
1. 방화벽 설정 확인
2. 포트 번호 확인
3. 네트워크 연결 상태 확인

### 성능 문제
1. 프레임 스킵 설정 조정
2. 압축 품질 조정
3. 해상도 및 FPS 조정

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다.

## 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 생성해 주세요.