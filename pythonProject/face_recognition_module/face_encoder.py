import face_recognition
import numpy as np
import cv2
import os
import pickle
import json

class FaceEncoder:
    def __init__(self, tolerance=0.6):
        self.tolerance = tolerance
        self.known_face_encodings = []
        self.known_face_ids = []
        
    def encode_face_from_image(self, image_path):
        """Extract face encoding from an image file"""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                return None, "No face detected in image"
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please use image with single face"
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) > 0:
                return face_encodings[0], "Success"
            else:
                return None, "Could not encode face"
                
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def encode_face_from_camera(self, frame, face_location=None):
        """Extract face encoding from camera frame"""
        try:
            # Convert BGR to RGB (OpenCV uses BGR, face_recognition uses RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if face_location is None:
                # Find face locations
                face_locations = face_recognition.face_locations(rgb_frame)
                if len(face_locations) == 0:
                    return None, None, "No face detected"
                face_location = face_locations[0]
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])
            
            if len(face_encodings) > 0:
                return face_encodings[0], face_location, "Success"
            else:
                return None, face_location, "Could not encode face"
                
        except Exception as e:
            return None, None, f"Error: {str(e)}"
    
    def compare_faces(self, unknown_encoding, known_encodings):
        """Compare unknown face encoding with known encodings"""
        if len(known_encodings) == 0:
            return False, None, 0
        
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, self.tolerance)
        face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        
        if True in matches:
            best_match_index = np.argmin(face_distances)
            confidence = 1 - face_distances[best_match_index]
            return True, best_match_index, confidence
        else:
            return False, None, 0
    
    def save_encoding(self, encoding, student_id, save_path):
        """Save face encoding to file"""
        encoding_data = {
            'student_id': student_id,
            'encoding': encoding.tolist()
        }
        
        # Ensure save path exists
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        filename = os.path.join(save_path, f"{student_id}.pkl")
        with open(filename, 'wb') as f:
            pickle.dump(encoding_data, f)
        
        return filename
    
    def load_encodings(self, load_path):
        """Load all face encodings from directory"""
        self.known_face_encodings = []
        self.known_face_ids = []
        
        if not os.path.exists(load_path):
            return [], []
        
        for filename in os.listdir(load_path):
            if filename.endswith('.pkl'):
                filepath = os.path.join(load_path, filename)
                try:
                    with open(filepath, 'rb') as f:
                        data = pickle.load(f)
                        self.known_face_encodings.append(np.array(data['encoding']))
                        self.known_face_ids.append(data['student_id'])
                except:
                    continue
        
        return self.known_face_encodings, self.known_face_ids
    
    def encoding_to_json(self, encoding):
        """Convert numpy encoding to JSON serializable format"""
        return json.dumps(encoding.tolist())
    
    def json_to_encoding(self, json_str):
        """Convert JSON string back to numpy encoding"""
        return np.array(json.loads(json_str))