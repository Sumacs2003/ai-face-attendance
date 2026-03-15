import cv2
import numpy as np
import threading
import time

class CameraHandler:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False
        self.frame = None
        self.lock = threading.Lock()
        self.thread = None
        
    def start_camera(self):
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                return False
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            self.thread = threading.Thread(target=self._update_frame)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False
    
    def _update_frame(self):
        """Continuously update frame in background"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                time.sleep(0.03)  # ~30 FPS
            except:
                break
    
    def get_frame(self):
        """Get current frame"""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
    
    def capture_image(self):
        """Capture a single image"""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.camera_id)
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def release_camera(self):
        """Release camera resources"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def draw_face_box(self, frame, face_location, name=None, confidence=None):
        """Draw rectangle around face and label"""
        if face_location and len(face_location) == 4:
            top, right, bottom, left = face_location
            
            # Draw rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Draw label
            if name:
                label = str(name)
                if confidence:
                    label += f" ({confidence:.2f})"
                
                # Draw label background
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                
                # Draw label text
                cv2.putText(frame, label, (left + 6, bottom - 6), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def is_camera_available(self):
        """Check if camera is available"""
        test_cap = cv2.VideoCapture(self.camera_id)
        available = test_cap.isOpened()
        test_cap.release()
        return available