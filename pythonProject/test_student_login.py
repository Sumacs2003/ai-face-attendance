# test_student_login.py
from app import create_app, db  # Fixed: Added db import
from app.models import StudentUser, Student


def test_login():
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("🔍 Testing Student Login Credentials")
        print("=" * 60)

        students = Student.query.all()
        for student in students:
            student_user = StudentUser.query.filter_by(student_id=student.id).first()
            if student_user:
                password = str(student.roll_number)
                if student_user.check_password(password):
                    print(f"✅ {student.name}: Username={student_user.username}, Password={password} ✓")
                else:
                    print(f"❌ {student.name}: Password mismatch! Resetting...")
                    student_user.set_password(password)
                    db.session.commit()
                    print(f"   Password reset to: {password}")
            else:
                print(f"❌ {student.name}: No login account found! Creating...")
                # Generate username
                name_part = student.name.lower().replace(' ', '')[:8]
                roll_part = str(student.roll_number).zfill(4)
                username = f"{name_part}_{roll_part}"

                student_user = StudentUser(
                    student_id=student.id,
                    username=username,
                    is_active=True
                )
                student_user.set_password(str(student.roll_number))
                db.session.add(student_user)
                db.session.commit()
                print(f"   Created: Username={username}, Password={student.roll_number}")

        print("\n" + "=" * 60)
        print("✅ Login credentials verified/fixed")
        print("=" * 60)


if __name__ == "__main__":
    test_login()