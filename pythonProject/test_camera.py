# test_camera.py
import cv2

print("Testing camera access...")

# Try different camera indices and backends
for camera_id in [0, 1, -1]:
    for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY, cv2.CAP_MSMF]:
        try:
            print(f"Trying camera {camera_id} with backend {backend}")
            cap = cv2.VideoCapture(camera_id, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"✅ SUCCESS! Camera {camera_id} is working!")
                    print(f"   Frame size: {frame.shape}")
                    cap.release()
                    exit(0)
                else:
                    print(f"❌ Camera opened but can't read frames")
                cap.release()
            else:
                print(f"❌ Cannot open camera {camera_id}")
        except Exception as e:
            print(f"❌ Error: {e}")

print("\n❌ No camera found working with Python")
print("\nTroubleshooting:")
print("1. Make sure no other app is using the camera")
print("2. Try restarting your computer")
print("3. Check if antivirus is blocking Python")