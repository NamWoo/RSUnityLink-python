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
    public Button startStreamingButton;
    public string serverUrl = "http://localhost:8080"; // Inspector에서 수정 가능하도록 public으로 변경

    private SocketIOUnity socket;
    private bool isConnected = false;

    void Start()
    {
        // Ensure UnityMainThreadDispatcher exists
        if (UnityMainThreadDispatcher.Instance() == null)
        {
            Debug.LogWarning("UnityMainThreadDispatcher not found, creating one...");
        }

        Debug.Log($"Attempting to connect to server at: {serverUrl}");
        
        try
        {
            var uri = new Uri(serverUrl);
            socket = new SocketIOUnity(uri, new SocketIOOptions
            {
                Transport = SocketIOClient.Transport.TransportProtocol.WebSocket,
                Reconnection = true,
                ReconnectionAttempts = 3,
                AutoUpgrade = false
            });

            SetupSocketEvents();
            socket.Connect();
        }
        catch (Exception e)
        {
            Debug.LogError($"Error initializing socket: {e.Message}");
            if (statusText != null) statusText.text = $"Error: {e.Message}";
        }
    }

    private void SetupSocketEvents()
    {
        socket.OnConnected += (sender, e) =>
        {
            Debug.Log("Socket connected successfully");
            isConnected = true;
            if (statusText != null)
            {
                UnityMainThreadDispatcher.Instance().Enqueue(() =>
                {
                    statusText.text = "Status: Connected";
                });
            }
        };

        socket.OnDisconnected += (sender, e) =>
        {
            Debug.LogWarning($"Socket disconnected: {e}");
            isConnected = false;
            if (statusText != null)
            {
                UnityMainThreadDispatcher.Instance().Enqueue(() =>
                {
                    statusText.text = "Status: Disconnected";
                });
            }
        };

        socket.OnError += (sender, e) =>
        {
            Debug.LogError($"Socket error: {e}");
            if (statusText != null)
            {
                UnityMainThreadDispatcher.Instance().Enqueue(() =>
                {
                    statusText.text = $"Error: {e}";
                });
            }
        };

        // Frame data handling
        socket.On("frame_data", (response) =>
        {
            Debug.Log($"Received frame data: {response}");
            try
            {
                var json = response.GetValue().ToString();
                var frame = JsonUtility.FromJson<FrameData>(json);

                UnityMainThreadDispatcher.Instance().Enqueue(() =>
                {
                    UpdateImages(frame);
                    UpdateIMUData(frame);
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"Error processing frame data: {e.Message}");
            }
        });

        socket.On("status", (response) =>
        {
            Debug.Log($"Received status: {response}");
            if (statusText != null)
            {
                UnityMainThreadDispatcher.Instance().Enqueue(() =>
                {
                    statusText.text = $"Status: {response.GetValue()}";
                });
            }
        });

        // Set up button listener
        if (startStreamingButton != null)
        {
            startStreamingButton.onClick.AddListener(() =>
            {
                if (isConnected)
                {
                    Debug.Log("Sending start_streaming request");
                    socket.EmitAsync("start_streaming", new { timestamp = DateTime.Now.ToString() });
                }
                else
                {
                    Debug.LogWarning("Cannot start streaming - not connected to server");
                    if (statusText != null) statusText.text = "Status: Not connected to server";
                }
            });
        }
        else
        {
            Debug.LogError("Start Streaming Button not assigned in inspector!");
        }
    }

    private void UpdateImages(FrameData frame)
    {
        if (frame.color_image != null && !string.IsNullOrEmpty(frame.color_image.data))
        {
            try
            {
                if (colorImageDisplay != null)
                {
                    byte[] colorBytes = Convert.FromBase64String(frame.color_image.data);
                    Texture2D tex = new Texture2D(frame.color_image.width, frame.color_image.height, TextureFormat.RGB24, false);
                    tex.LoadImage(colorBytes);
                    colorImageDisplay.texture = tex;
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"Error updating color image: {e.Message}");
            }
        }

        if (frame.depth_image != null && !string.IsNullOrEmpty(frame.depth_image.data))
        {
            try
            {
                if (depthImageDisplay != null)
                {
                    byte[] depthBytes = Convert.FromBase64String(frame.depth_image.data);
                    Texture2D tex = new Texture2D(frame.depth_image.width, frame.depth_image.height, TextureFormat.RGB24, false);
                    tex.LoadImage(depthBytes);
                    depthImageDisplay.texture = tex;
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"Error updating depth image: {e.Message}");
            }
        }
    }

    private void UpdateIMUData(FrameData frame)
    {
        if (frame.imu != null && imuText != null)
        {
            imuText.text = $"IMU Data:\n" +
                $"Gyro: {frame.imu.gyroscope.x:F2}, {frame.imu.gyroscope.y:F2}, {frame.imu.gyroscope.z:F2}\n" +
                $"Accel: {frame.imu.accelerometer.x:F2}, {frame.imu.accelerometer.y:F2}, {frame.imu.accelerometer.z:F2}\n" +
                $"Temp: {frame.imu.temperature:F1}°C";
        }
    }

    void OnDestroy()
    {
        if (socket != null)
        {
            socket.Disconnect();
        }
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
