# fix_new_student_login.py
from app import create_app, db
from app.models import Student, StudentUser


def fix_student_login(student_name=None):
    """Fix login for a specific student or all students"""
    app = create_app()
    with app.app_context():
        if student_name:
            students = Student.query.filter(Student.name.contains(student_name)).all()
        else:
            students = Student.query.all()

        print("\n" + "=" * 70)
        print("🔧 FIXING STUDENT LOGIN ACCOUNTS")
        print("=" * 70)

        fixed = 0
        for student in students:
            print(f"\n▶ Processing: {student.name} (ID: {student.id})")
            print(f"   Roll: {student.roll_number}")

            # Generate username
            name_part = student.name.lower().replace(' ', '')[:8]
            roll_str = str(student.roll_number).strip()
            roll_part = roll_str.zfill(4)
            username = f"{name_part}_{roll_part}"
            password = roll_str

            # Check if account exists
            existing = StudentUser.query.filter_by(student_id=student.id).first()

            if existing:
                print(f"   🔄 Account exists - Updating...")
                print(f"     Old username: {existing.username}")
                print(f"     New username: {username}")
                existing.username = username
                existing.set_password(password)
                db.session.commit()
                print(f"   ✅ Updated: {username} / {password}")
                fixed += 1
            else:
                print(f"   ✨ Creating new account...")
                student_user = StudentUser(
                    student_id=student.id,
                    username=username,
                    is_active=True
                )
                student_user.set_password(password)
                db.session.add(student_user)
                db.session.commit()
                print(f"   ✅ Created: {username} / {password}")
                fixed += 1

        print("\n" + "=" * 70)
        print(f"✅ Fixed {fixed} student login accounts")
        print("=" * 70)


def check_student_login(student_name):
    """Check if a specific student can login"""
    app = create_app()
    with app.app_context():
        student = Student.query.filter(Student.name.contains(student_name)).first()

        if not student:
            print(f"❌ Student '{student_name}' not found")
            return

        print(f"\n🔍 Checking login for: {student.name}")
        print(f"   Student ID: {student.student_id}")
        print(f"   Roll Number: {student.roll_number}")

        student_user = StudentUser.query.filter_by(student_id=student.id).first()

        if student_user:
            print(f"   ✅ Account exists")
            print(f"   Username: {student_user.username}")
            print(f"   Password: {student.roll_number}")
            print(f"   Active: {student_user.is_active}")

            # Test password
            if student_user.check_password(str(student.roll_number)):
                print(f"   ✅ Password is correct")
                print(f"\n📋 LOGIN WITH:")
                print(f"   Username: {student_user.username}")
                print(f"   Password: {student.roll_number}")
            else:
                print(f"   ❌ Password is incorrect - fixing...")
                student_user.set_password(str(student.roll_number))
                db.session.commit()
                print(f"   ✅ Password fixed to: {student.roll_number}")
        else:
            print(f"   ❌ No account found - creating...")
            name_part = student.name.lower().replace(' ', '')[:8]
            roll_str = str(student.roll_number).strip()
            roll_part = roll_str.zfill(4)
            username = f"{name_part}_{roll_part}"

            student_user = StudentUser(
                student_id=student.id,
                username=username,
                is_active=True
            )
            student_user.set_password(roll_str)
            db.session.add(student_user)
            db.session.commit()
            print(f"   ✅ Created: {username} / {roll_str}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--check" and len(sys.argv) > 2:
            check_student_login(sys.argv[2])
        elif sys.argv[1] == "--fix" and len(sys.argv) > 2:
            fix_student_login(sys.argv[2])
        else:
            fix_student_login()
    else:
        fix_student_login()