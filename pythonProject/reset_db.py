# reset_db.py - Use this ONLY when you want to completely reset the database
import os
import shutil
from app import create_app, db
from app.models import User, Student, Attendance, FaceEncoding, Class, Settings, StudentUser, LeaveRequest
from datetime import datetime


def reset_database():
    print("=" * 60)
    print("🔄 Face Attendance System - Database Reset")
    print("=" * 60)
    print("⚠️  WARNING: This will DELETE ALL EXISTING DATA!")
    confirm = input("Type 'YES' to confirm: ")

    if confirm != "YES":
        print("❌ Reset cancelled.")
        return

    # Backup old database if exists
    db_path = 'database/attendance.db'
    if os.path.exists(db_path):
        backup_path = f'database/attendance_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created at {backup_path}")

        # Delete old database
        os.remove(db_path)
        print("✅ Old database deleted.")

    # Create new database with updated schema
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ New database created!")

        # Create admin
        admin = User(username='admin', email='admin@example.com', is_admin=True, is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)

        # Create teacher
        teacher = User(username='teacher', email='teacher@example.com', is_teacher=True,
                       is_active=True, teacher_id='TCH001', department='CS')
        teacher.set_password('teacher123')
        db.session.add(teacher)

        # Create students
        students = [
            {'student_id': 'STU-001', 'name': 'John Doe', 'roll_number': '2024001', 'class_name': 'Class 10',
             'section': 'A'},
            {'student_id': 'STU-002', 'name': 'Jane Smith', 'roll_number': '2024002', 'class_name': 'Class 10',
             'section': 'A'},
        ]
        for s in students:
            db.session.add(Student(**s, admission_date=datetime.utcnow().date()))

        # Create classes
        classes = [
            {'name': 'Class 9', 'section': 'A', 'academic_year': '2024-2025'},
            {'name': 'Class 9', 'section': 'B', 'academic_year': '2024-2025'},
            {'name': 'Class 10', 'section': 'A', 'academic_year': '2024-2025'},
        ]
        for c in classes:
            db.session.add(Class(**c))

        db.session.commit()

        # Create student login accounts
        from app.models import StudentUser
        for student in Student.query.all():
            if not StudentUser.query.filter_by(student_id=student.id).first():
                name_part = student.name.lower().replace(' ', '')[:8]
                username = f"{name_part}_{student.roll_number[-4:]}"
                student_user = StudentUser(student_id=student.id, username=username)
                student_user.set_password(student.roll_number)
                db.session.add(student_user)
        db.session.commit()

        # Create settings
        default_settings = [
            {'key': 'site_name', 'value': 'Face Attendance System'},
            {'key': 'items_per_page', 'value': '10'},
            {'key': 'attendance_threshold', 'value': '0.6'},
        ]
        for default in default_settings:
            db.session.add(Settings(**default))
        db.session.commit()

        print("\n📊 Database Summary:")
        print(f"   - Users: {User.query.count()}")
        print(f"   - Students: {Student.query.count()}")
        print(f"   - Classes: {Class.query.count()}")

    print("\n" + "=" * 60)
    print("✅ Reset complete!")
    print("=" * 60)
    print("🔑 Admin: admin / admin123")
    print("🔑 Teacher: teacher / teacher123")
    print("=" * 60)


if __name__ == "__main__":
    reset_database()