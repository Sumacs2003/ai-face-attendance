from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
import logging

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Set up login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Ensure required directories exist
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'faces'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'captured_faces'), exist_ok=True)
    os.makedirs('database', exist_ok=True)
    os.makedirs('database/backups', exist_ok=True)
    os.makedirs('database/exports', exist_ok=True)
    os.makedirs('database/temp', exist_ok=True)

    # Create database directory if it doesn't exist
    db_path = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    if db_path:
        os.makedirs(db_path, exist_ok=True)

    # Register blueprints
    from app.routes import auth_bp, main_bp, staff_bp, attendance_bp, face_bp
    from app.student_routes import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(face_bp)
    app.register_blueprint(student_bp)

    # Create database tables WITHOUT dropping existing data
    with app.app_context():
        # ✅ FIXED: REMOVED db.drop_all() - This was deleting all your data!
        db.create_all()  # This only creates tables if they don't exist

        # Check if admin user exists before creating
        from app.models import User
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Default admin user created - Username: admin, Password: admin123')

        # Check if teacher user exists
        if not User.query.filter_by(username='teacher').first():
            teacher = User(
                username='teacher',
                email='teacher@example.com',
                is_teacher=True,
                is_active=True,
                teacher_id='TCH001',
                department='Computer Science',
                phone='1234567890'
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            db.session.commit()
            print('✅ Default teacher user created - Username: teacher, Password: teacher123')

        # Initialize default settings only if they don't exist
        from app.models import Settings
        default_settings = [
            {'key': 'site_name', 'value': 'Face Attendance System', 'description': 'Site name displayed in browser'},
            {'key': 'items_per_page', 'value': '10', 'description': 'Items per page in tables'},
            {'key': 'attendance_threshold', 'value': '0.6', 'description': 'Face recognition threshold'},
            {'key': 'auto_refresh_interval', 'value': '30', 'description': 'Auto refresh interval in seconds'},
            {'key': 'session_timeout', 'value': '30', 'description': 'Session timeout in minutes'},
            {'key': 'max_login_attempts', 'value': '5', 'description': 'Maximum login attempts before lockout'},
        ]

        for default in default_settings:
            if not Settings.query.filter_by(key=default['key']).first():
                setting = Settings(**default)
                db.session.add(setting)
        db.session.commit()
        print('✅ Default settings initialized (if not existed)')

        # Create default classes only if none exist
        from app.models import Class
        if Class.query.count() == 0:
            classes = [
                {'name': 'Class 9', 'section': 'A', 'description': 'Grade 9 Section A', 'academic_year': '2024-2025'},
                {'name': 'Class 9', 'section': 'B', 'description': 'Grade 9 Section B', 'academic_year': '2024-2025'},
                {'name': 'Class 10', 'section': 'A', 'description': 'Grade 10 Section A', 'academic_year': '2024-2025'},
                {'name': 'Class 10', 'section': 'B', 'description': 'Grade 10 Section B', 'academic_year': '2024-2025'},
            ]
            for class_data in classes:
                class_obj = Class(**class_data)
                db.session.add(class_obj)
            db.session.commit()
            print('✅ Default classes created')

    return app