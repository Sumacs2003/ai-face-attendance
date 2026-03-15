import os
import json
import base64
import numpy as np
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import face_recognition
from flask import current_app
from app import db
from app.models import Student, Attendance, FaceEncoding, User


def allowed_file(filename, allowed_extensions=None):
    """
    Check if file has allowed extension
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder=None):
    """
    Save uploaded file and return filename
    """
    if upload_folder is None:
        upload_folder = current_app.config['UPLOAD_FOLDER']

    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)

        # Add timestamp to filename to make it unique
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"

        # Ensure upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Save file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        return filename
    return None


def get_attendance_stats(period='week', class_name=None):
    """
    Get attendance statistics for charts
    """
    today = date.today()

    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    elif period == 'year':
        days = 365
    else:
        days = 7

    dates = []
    counts = []

    query = db.session.query(Attendance.student_id)

    if class_name:
        query = query.join(Student).filter(Student.class_name == class_name)

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        count = query.filter(Attendance.date == day).distinct().count()

        dates.append(day.strftime('%d %b'))
        counts.append(count)

    return {
        'labels': dates,
        'data': counts,
        'total': sum(counts),
        'average': round(sum(counts) / days if days > 0 else 0, 2)
    }


def encode_face_from_image(image_path):
    """
    Extract face encoding from image file
    """
    try:
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            return None

        # Load image
        image = face_recognition.load_image_file(image_path)

        # Detect faces
        face_locations = face_recognition.face_locations(image)

        if not face_locations:
            print("No face detected in image")
            return None

        # Get face encodings
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if face_encodings:
            # Return the first face encoding as a list
            return face_encodings[0].tolist()
        return None

    except Exception as e:
        print(f"Error encoding face: {e}")
        return None


def encode_face_from_base64(base64_image):
    """
    Extract face encoding from base64 image string
    """
    try:
        # Remove header if present
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]

        # Decode base64
        image_bytes = base64.b64decode(base64_image)

        # Convert to numpy array
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_img)

        if not face_locations:
            return None

        # Get face encodings
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

        if face_encodings:
            return face_encodings[0].tolist()
        return None

    except Exception as e:
        print(f"Error encoding face from base64: {e}")
        return None


def compare_faces(unknown_encoding, threshold=0.6):
    """
    Compare unknown face with all known faces
    """
    try:
        # Get all known face encodings
        known_faces = FaceEncoding.query.all()

        if not known_faces:
            return None

        # Convert unknown encoding to numpy array
        unknown_encoding_np = np.array(unknown_encoding)

        # Prepare known encodings
        known_encodings = []
        student_ids = []

        for face in known_faces:
            try:
                encoding = np.array(json.loads(face.encoding))
                known_encodings.append(encoding)
                student_ids.append(face.student_id)
            except:
                continue

        if not known_encodings:
            return None

        # Compare faces
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding_np)
        face_distances = face_recognition.face_distance(known_encodings, unknown_encoding_np)

        # Find best match
        best_match_index = np.argmin(face_distances)
        confidence = 1 - face_distances[best_match_index]

        if matches[best_match_index] and confidence >= threshold:
            student = Student.query.get(student_ids[best_match_index])
            if student:
                return {
                    'student_id': student.id,
                    'student_name': student.name,
                    'roll_number': student.roll_number,
                    'confidence': float(confidence)
                }

        return None

    except Exception as e:
        print(f"Error comparing faces: {e}")
        return None


def generate_student_id():
    """
    Generate unique student ID
    """
    last_student = Student.query.order_by(Student.id.desc()).first()

    if last_student and last_student.student_id:
        try:
            # Extract number from existing ID (e.g., STU-001 -> 1)
            last_num = int(last_student.student_id.split('-')[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1

    return f"STU-{str(new_num).zfill(4)}"


def format_datetime(value, format='%d %b %Y %I:%M %p'):
    """
    Format datetime for templates
    """
    if value is None:
        return ''
    return value.strftime(format)


def calculate_attendance_percentage(student_id, from_date=None, to_date=None):
    """
    Calculate attendance percentage for a student
    """
    if from_date is None:
        from_date = date.today() - timedelta(days=30)
    if to_date is None:
        to_date = date.today()

    # Calculate total days (excluding Sundays)
    total_days = 0
    current = from_date
    while current <= to_date:
        if current.weekday() != 6:  # Skip Sunday (6)
            total_days += 1
        current += timedelta(days=1)

    present_days = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= from_date,
        Attendance.date <= to_date
    ).count()

    if total_days > 0:
        return round((present_days / total_days) * 100, 2)
    return 0


def get_dashboard_stats(user_id=None, is_admin=False):
    """
    Get dashboard statistics based on user role
    """
    today = date.today()

    stats = {
        'total_students': Student.query.count(),
        'total_classes': Class.query.count() if has_db_model('Class') else 0,
        'today_date': today.strftime('%Y-%m-%d'),
        'current_time': datetime.now().strftime('%H:%M:%S')
    }

    if is_admin:
        # Admin sees all attendance
        stats['today_attendance'] = db.session.query(Attendance.student_id).filter(
            Attendance.date == today
        ).distinct().count()

        # Recent attendance
        stats['recent_attendance'] = Attendance.query.order_by(
            Attendance.timestamp.desc()
        ).limit(10).all()

        # Attendance trend
        trend = get_attendance_stats('month')
        stats['attendance_labels'] = trend['labels']
        stats['attendance_data'] = trend['data']

    else:
        # Teacher might see filtered stats
        stats['today_attendance'] = 0
        stats['recent_attendance'] = []
        stats['attendance_labels'] = []
        stats['attendance_data'] = []

    return stats


def has_db_model(model_name):
    """
    Check if a database model exists
    """
    try:
        from app.models import Class
        return True
    except:
        return False


def create_notification(message, type='info', user_id=None):
    """
    Create a notification for user
    """
    # This would need a Notification model
    # Placeholder for future implementation
    pass


def log_activity(user_id, action, details=None):
    """
    Log user activity
    """
    # This would need an ActivityLog model
    # Placeholder for future implementation
    pass