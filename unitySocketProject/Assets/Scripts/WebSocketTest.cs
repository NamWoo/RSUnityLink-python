using System;
using System.Collections.Generic;
using UnityEngine;
using SocketIOClient;
using TMPro; // TextMeshPro 사용시
using UnityEngine.UI; // UnityEngine.UI 사용시
using TMPro;

public class WebSocketTest : MonoBehaviour
{
    public RawImage colorImageDisplay;
    public RawImage depthImageDisplay;
    public TextMeshProUGUI statusText;
    public TextMeshProUGUI imuText;

    private SocketIOUnity socket;

    void Start()
    {
        var uri = new Uri("http://192.168.45.236:8080"); // 서버 주소/포트에 맞게 수정
        socket = new SocketIOUnity(uri, new SocketIOOptions
        {
            Transport = SocketIOClient.Transport.TransportProtocol.WebSocket
        });

        socket.OnConnected += (sender, e) =>
        {
            Debug.Log("연결됨");
            if (statusText != null) statusText.text = "상태: 연결됨";
        };
        socket.OnDisconnected += (sender, e) =>
        {
            Debug.Log("연결 해제: " + e);
            if (statusText != null) statusText.text = "상태: 연결 해제";
        };

        // 프레임 데이터 수신
        socket.On("frame_data", (response) =>
        {
            Debug.Log("frame_data 수신: " + response);
            var json = response.GetValue().ToString();
            var frame = JsonUtility.FromJson<FrameData>(json);

            // 컬러 이미지 표시
            if (frame.color_image != null && !string.IsNullOrEmpty(frame.color_image.data))
            {
                byte[] colorBytes = Convert.FromBase64String(frame.color_image.data);
                Texture2D tex = new Texture2D(frame.color_image.width, frame.color_image.height, TextureFormat.RGB24, false);
                tex.LoadImage(colorBytes);
                colorImageDisplay.texture = tex;
            }

            // 뎁스 이미지 표시
            if (frame.depth_image != null && !string.IsNullOrEmpty(frame.depth_image.data))
            {
                byte[] depthBytes = Convert.FromBase64String(frame.depth_image.data);
                Texture2D tex = new Texture2D(frame.depth_image.width, frame.depth_image.height, TextureFormat.RGB24, false);
                tex.LoadImage(depthBytes);
                depthImageDisplay.texture = tex;
            }

            // IMU 데이터 표시
            if (frame.imu != null && imuText != null)
            {
                imuText.text = $"IMU\n" +
                    $"Gyro: {frame.imu.gyroscope.x:F2}, {frame.imu.gyroscope.y:F2}, {frame.imu.gyroscope.z:F2}\n" +
                    $"Accel: {frame.imu.accelerometer.x:F2}, {frame.imu.accelerometer.y:F2}, {frame.imu.accelerometer.z:F2}\n" +
                    $"Temp: {frame.imu.temperature:F1}°C";
            }
        });

        // 상태 메시지 수신
        socket.On("status", (response) =>
        {
            Debug.Log("status 수신: " + response);
            if (statusText != null) statusText.text = "상태: " + response.GetValue().ToString();
        });

        socket.Connect();
    }

    // 데이터 구조 정의 (JsonUtility 사용을 위해 C# 구조체로 정의)
    [Serializable]
    public class FrameData
    {
        public ImageData color_image;
        public ImageData depth_image;
        public IMUData imu;
    }

    [Serializable]
    public class ImageData
    {
        public string data;
        public int width;
        public int height;
        public string format;
    }

    [Serializable]
    public class IMUData
    {
        public GyroscopeData gyroscope;
        public AccelerometerData accelerometer;
        public float temperature;
    }

    [Serializable]
    public class GyroscopeData
    {
        public float x, y, z;
    }

    [Serializable]
    public class AccelerometerData
    {
        public float x, y, z;
    }
}
