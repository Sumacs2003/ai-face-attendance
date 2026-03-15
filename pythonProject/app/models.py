from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    # Check if it's a staff user (prefixed with 'staff_')
    if user_id.startswith('staff_'):
        return User.query.get(int(user_id.replace('staff_', '')))
    # Check if it's a student user (prefixed with 'student_')
    elif user_id.startswith('student_'):
        return StudentUser.query.get(int(user_id.replace('student_', '')))
    return None


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)  # UNIQUE CONSTRAINT REMOVED
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_teacher = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Teacher specific fields
    teacher_id = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"staff_{self.id}"

    # Permission methods
    def can_add_student(self):
        return self.is_admin

    def can_edit_student(self):
        return self.is_admin or self.is_teacher

    def can_delete_student(self):
        return self.is_admin

    def can_register_face(self):
        return self.is_admin

    def can_view_reports(self):
        return self.is_admin or self.is_teacher

    def can_view_students(self):
        return True

    def can_take_attendance(self):
        return self.is_admin or self.is_teacher

    def can_view_attendance(self):
        return True

    def can_manage_settings(self):
        return self.is_admin

    def __repr__(self):
        return f'<User {self.username}>'


class StudentUser(UserMixin, db.Model):
    __tablename__ = 'student_users'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    student = db.relationship('Student', backref='user_account', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"student_{self.id}"

    def __repr__(self):
        return f'<StudentUser {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    class_name = db.Column(db.String(50))
    section = db.Column(db.String(10))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    photo_path = db.Column(db.String(200))
    face_encoded = db.Column(db.Boolean, default=False)
    parent_name = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    admission_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attendances = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    face_encodings = db.relationship('FaceEncoding', backref='student', lazy=True, cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present')  # present, absent, late, holiday
    confidence = db.Column(db.Float, default=1.0)
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    remarks = db.Column(db.String(200))

    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance_per_day'),)

    def __repr__(self):
        return f'<Attendance {self.student_id} on {self.date}>'


class FaceEncoding(db.Model):
    __tablename__ = 'face_encodings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    encoding = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FaceEncoding for student {self.student_id}>'


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    remarks = db.Column(db.Text)
    requested_on = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_on = db.Column(db.DateTime)

    def __repr__(self):
        return f'<LeaveRequest {self.student_id} - {self.status}>'


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    description = db.Column(db.Text, default='')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('name', 'section', 'academic_year', name='unique_class'),)

    # Relationship
    teacher = db.relationship('User', foreign_keys=[teacher_id])

    def __repr__(self):
        return f'<Class {self.name} - {self.section}>'


class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Settings {self.key}>'