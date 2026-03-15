import cv2
import numpy as np
from .face_encoder import FaceEncoder
import os

class FaceRecognizer:
    def __init__(self, encodings_path, tolerance=0.6):
        self.encoder = FaceEncoder(tolerance)
        self.encodings_path = encodings_path
        self.known_encodings = []
        self.known_ids = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known face encodings"""
        if os.path.exists(self.encodings_path):
            self.known_encodings, self.known_ids = self.encoder.load_encodings(self.encodings_path)
        return len(self.known_encodings)
    
    def recognize_face(self, frame):
        """Recognize face in frame"""
        # Get face encoding from frame
        encoding, face_location, message = self.encoder.encode_face_from_camera(frame)
        
        if encoding is None:
            return None, None, None, face_location, message
        
        # Compare with known faces
        if len(self.known_encodings) > 0:
            match, index, confidence = self.encoder.compare_faces(encoding, self.known_encodings)
            
            if match and confidence > 0.5:  # Threshold for recognition
                student_id = self.known_ids[index]
                return student_id, encoding, confidence, face_location, "Face recognized"
            else:
                return None, encoding, None, face_location, "Unknown face"
        else:
            return None, encoding, None, face_location, "No known faces in database"
    
    def add_new_face(self, student_id, encoding):
        """Add new face encoding to known faces"""
        self.known_encodings.append(encoding)
        self.known_ids.append(student_id)
        
        # Save to file
        self.encoder.save_encoding(encoding, student_id, self.encodings_path)
        
        return True
    
    def remove_face(self, student_id):
        """Remove face encoding by student ID"""
        if student_id in self.known_ids:
            index = self.known_ids.index(student_id)
            self.known_encodings.pop(index)
            self.known_ids.pop(index)
            
            # Remove file
            filepath = os.path.join(self.encodings_path, f"{student_id}.pkl")
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        return False
    
    def get_known_faces_count(self):
        """Get number of known faces"""
        return len(self.known_ids)