# fix_all_student_logins.py
from app import create_app, db
from app.models import Student, StudentUser


def fix_all_student_logins():
    """Fix all student login accounts"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("🔧 FIXING ALL STUDENT LOGIN ACCOUNTS")
        print("=" * 70)

        students = Student.query.all()
        fixed_count = 0

        for student in students:
            print(f"\n▶ Processing: {student.name}")
            print(f"   ID: {student.student_id}")
            print(f"   Roll: {student.roll_number}")

            # Generate username correctly
            name_part = student.name.lower().replace(' ', '')[:8]
            roll_str = str(student.roll_number).strip()
            roll_part = roll_str.zfill(4)
            username = f"{name_part}_{roll_part}"
            password = roll_str

            # Check if account exists
            existing = StudentUser.query.filter_by(student_id=student.id).first()

            if existing:
                print(f"   🔄 Updating existing account")
                print(f"     Old username: {existing.username}")
                print(f"     New username: {username}")
                existing.username = username
                existing.set_password(password)
                print(f"     Password set to: {password}")
                fixed_count += 1
            else:
                print(f"   ✨ Creating new account")
                student_user = StudentUser(
                    student_id=student.id,
                    username=username,
                    is_active=True
                )
                student_user.set_password(password)
                db.session.add(student_user)
                print(f"     Username: {username}")
                print(f"     Password: {password}")
                fixed_count += 1

            db.session.commit()

        print("\n" + "=" * 70)
        print(f"✅ Fixed {fixed_count} student login accounts")
        print("=" * 70)

        # Show all credentials
        print("\n📋 ALL STUDENT LOGIN CREDENTIALS:")
        print("-" * 70)
        for student_user in StudentUser.query.all():
            student = student_user.student
            print(f"Name: {student.name}")
            print(f"Username: {student_user.username}")
            print(f"Password: {student.roll_number}")
            print(f"Student ID: {student.student_id}")
            print("-" * 40)


if __name__ == "__main__":
    fix_all_student_logins()