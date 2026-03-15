#!/usr/bin/env python
"""
Database Initialization Script for Face Attendance System
Run this script to create database tables and populate with sample data
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import create_app, db
    from app.models import User, Student, Attendance, FaceEncoding, Class, Settings
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the correct directory and virtual environment is activated")
    sys.exit(1)


def init_database():
    """Initialize database with sample data"""

    # Create app context
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("  FACE ATTENDANCE SYSTEM - DATABASE INITIALIZATION")
        print("=" * 60)

        # Drop all tables and recreate
        print("\n[1/7] Dropping existing tables...")
        db.drop_all()
        print("  ✓ Tables dropped")

        print("\n[2/7] Creating new tables...")
        db.create_all()
        print("  ✓ Tables created")

        # Create admin user
        print("\n[3/7] Creating admin user...")
        try:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("  ✓ Admin user created (admin/admin123)")
        except Exception as e:
            print(f"  ✗ Error creating admin: {e}")
            db.session.rollback()

        # Create teacher user
        print("\n[4/7] Creating teacher user...")
        try:
            teacher = User(
                username='teacher',
                email='teacher@example.com',
                is_admin=False,
                is_active=True
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            print("  ✓ Teacher user created (teacher/teacher123)")
        except Exception as e:
            print(f"  ✗ Error creating teacher: {e}")
            db.session.rollback()

        # Commit users
        db.session.commit()

        # Create sample students
        print("\n[5/7] Creating sample students...")
        students = []
        sample_students = [
            {
                'student_id': 'STU-001',
                'name': 'John Doe',
                'roll_number': 'CS001',
                'class_name': 'Computer Science',
                'section': 'A',
                'email': 'john.doe@example.com',
                'phone': '1234567890',
                'address': '123 Main St, City',
                'face_encoded': False
            },
            {
                'student_id': 'STU-002',
                'name': 'Jane Smith',
                'roll_number': 'CS002',
                'class_name': 'Computer Science',
                'section': 'A',
                'email': 'jane.smith@example.com',
                'phone': '0987654321',
                'address': '456 Oak Ave, Town',
                'face_encoded': False
            },
            {
                'student_id': 'STU-003',
                'name': 'Bob Johnson',
                'roll_number': 'CS003',
                'class_name': 'Computer Science',
                'section': 'B',
                'email': 'bob.johnson@example.com',
                'phone': '5551234567',
                'address': '789 Pine Rd, Village',
                'face_encoded': False
            },
            {
                'student_id': 'STU-004',
                'name': 'Alice Brown',
                'roll_number': 'CS004',
                'class_name': 'Computer Science',
                'section': 'B',
                'email': 'alice.brown@example.com',
                'phone': '7778889999',
                'address': '321 Elm St, County',
                'face_encoded': False
            },
            {
                'student_id': 'STU-005',
                'name': 'Charlie Wilson',
                'roll_number': 'CS005',
                'class_name': 'Computer Science',
                'section': 'A',
                'email': 'charlie.wilson@example.com',
                'phone': '4445556666',
                'address': '654 Maple Dr, State',
                'face_encoded': False
            },
            {
                'student_id': 'STU-006',
                'name': 'Diana Prince',
                'roll_number': 'CS006',
                'class_name': 'Computer Science',
                'section': 'C',
                'email': 'diana.prince@example.com',
                'phone': '1112223333',
                'address': '987 Cedar Ln, Country',
                'face_encoded': False
            },
            {
                'student_id': 'STU-007',
                'name': 'Ethan Hunt',
                'roll_number': 'CS007',
                'class_name': 'Computer Science',
                'section': 'C',
                'email': 'ethan.hunt@example.com',
                'phone': '2223334444',
                'address': '135 Spruce Way, Province',
                'face_encoded': False
            },
            {
                'student_id': 'STU-008',
                'name': 'Fiona Glen',
                'roll_number': 'CS008',
                'class_name': 'Computer Science',
                'section': 'A',
                'email': 'fiona.glen@example.com',
                'phone': '3334445555',
                'address': '246 Birch Blvd, District',
                'face_encoded': False
            }
        ]

        try:
            for student_data in sample_students:
                student = Student(**student_data)
                db.session.add(student)
                students.append(student)

            db.session.commit()
            print(f"  ✓ {len(students)} students created")
        except Exception as e:
            print(f"  ✗ Error creating students: {e}")
            db.session.rollback()

        # Create sample classes
        print("\n[6/7] Creating sample classes...")
        classes = []
        sample_classes = [
            {'name': 'Mathematics 101', 'section': 'A', 'subject': 'Mathematics', 'teacher_id': 2},
            {'name': 'Physics 101', 'section': 'B', 'subject': 'Physics', 'teacher_id': 2},
            {'name': 'Chemistry 101', 'section': 'C', 'subject': 'Chemistry', 'teacher_id': 2},
            {'name': 'Computer Science 101', 'section': 'A', 'subject': 'Computer Science', 'teacher_id': 2},
            {'name': 'English Literature', 'section': 'B', 'subject': 'English', 'teacher_id': 2}
        ]

        try:
            for class_data in sample_classes:
                class_obj = Class(**class_data)
                db.session.add(class_obj)
                classes.append(class_obj)

            db.session.commit()
            print(f"  ✓ {len(classes)} classes created")
        except Exception as e:
            print(f"  ✗ Error creating classes: {e}")
            db.session.rollback()

        # Create sample attendance records
        print("\n[7/7] Creating sample attendance records...")
        attendance_count = 0
        today = datetime.now().date()

        try:
            # Generate attendance for last 30 days
            for days_ago in range(30, 0, -1):
                current_date = today - timedelta(days=days_ago)

                # Skip Sundays (day 6 is Sunday in Python where Monday=0)
                if current_date.weekday() == 6:
                    continue

                # For each student, randomly decide if present (80% chance)
                for student in students:
                    if random.random() < 0.8:  # 80% attendance rate
                        # Random time between 8:00 AM and 10:00 AM
                        hour = random.randint(8, 10)
                        minute = random.randint(0, 59)
                        second = random.randint(0, 59)

                        timestamp = datetime(
                            current_date.year,
                            current_date.month,
                            current_date.day,
                            hour, minute, second
                        )

                        # Random confidence between 0.85 and 1.0
                        confidence = round(random.uniform(0.85, 1.0), 2)

                        attendance = Attendance(
                            student_id=student.id,
                            date=current_date,
                            timestamp=timestamp,
                            status='present',
                            confidence=confidence,
                            marked_by=1  # Admin marked
                        )
                        db.session.add(attendance)
                        attendance_count += 1

            db.session.commit()
            print(f"  ✓ {attendance_count} attendance records created")
        except Exception as e:
            print(f"  ✗ Error creating attendance: {e}")
            db.session.rollback()

        # Create system settings
        print("\nCreating system settings...")
        settings = [
            {'key': 'school_name', 'value': 'Face Attendance School'},
            {'key': 'academic_year', 'value': '2024-2025'},
            {'key': 'attendance_start_time', 'value': '08:00'},
            {'key': 'attendance_end_time', 'value': '17:00'},
            {'key': 'late_threshold', 'value': '09:00'},
            {'key': 'face_recognition_threshold', 'value': '0.6'},
            {'key': 'enable_notifications', 'value': 'true'},
            {'key': 'default_confidence_threshold', 'value': '0.7'}
        ]

        try:
            for setting in settings:
                s = Settings(**setting)
                db.session.add(s)

            db.session.commit()
            print(f"  ✓ {len(settings)} settings created")
        except Exception as e:
            print(f"  ✗ Error creating settings: {e}")
            db.session.rollback()

        # Final summary
        print("\n" + "=" * 60)
        print("  DATABASE INITIALIZATION COMPLETE!")
        print("=" * 60)
        print("\n📊 SUMMARY:")
        print(f"  • Users: 2 (1 Admin, 1 Teacher)")
        print(f"  • Students: {len(students)}")
        print(f"  • Classes: {len(classes)}")
        print(f"  • Attendance Records: {attendance_count}")
        print(f"  • Settings: {len(settings)}")

        print("\n🔑 LOGIN CREDENTIALS:")
        print("  ┌─────────────┬─────────────┬─────────────┐")
        print("  │ Role        │ Username    │ Password    │")
        print("  ├─────────────┼─────────────┼─────────────┤")
        print("  │ Admin       │ admin       │ admin123    │")
        print("  │ Teacher     │ teacher     │ teacher123  │")
        print("  └─────────────┴─────────────┴─────────────┘")

        print("\n📁 DATABASE LOCATION:")
        print(f"  {app.config['SQLALCHEMY_DATABASE_URI']}")

        print("\n🚀 NEXT STEPS:")
        print("  1. Run the application: python run.py")
        print("  2. Open browser: http://localhost:5000")
        print("  3. Login with admin or teacher credentials")

        print("\n" + "=" * 60)
        print("  System ready! Happy coding! 🎉")
        print("=" * 60)


def check_database():
    """Check if database exists and has tables"""
    app = create_app()
    with app.app_context():
        try:
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if tables:
                print(f"\nDatabase found with tables: {', '.join(tables)}")
                return True
            else:
                print("\nDatabase exists but no tables found.")
                return False
        except Exception as e:
            print(f"\nDatabase not found or error accessing: {e}")
            return False


def reset_database():
    """Reset database (drop all tables and recreate)"""
    app = create_app()
    with app.app_context():
        confirm = input("\n⚠️  WARNING: This will delete ALL data! Continue? (y/N): ")
        if confirm.lower() == 'y':
            db.drop_all()
            db.create_all()
            print("✅ Database reset successfully!")
            return True
        else:
            print("❌ Reset cancelled.")
            return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Initialize Face Attendance System Database')
    parser.add_argument('--reset', action='store_true', help='Reset database before initialization')
    parser.add_argument('--check', action='store_true', help='Check database status')

    args = parser.parse_args()

    if args.check:
        check_database()
    elif args.reset:
        if reset_database():
            init_database()
    else:
        # Check if database already exists
        if check_database():
            confirm = input("\nDatabase already exists. Reinitialize? (y/N): ")
            if confirm.lower() == 'y':
                init_database()
            else:
                print("Initialization cancelled.")
        else:
            init_database()