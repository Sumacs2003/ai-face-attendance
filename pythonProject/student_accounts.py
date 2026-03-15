# create_student_accounts.py
from app import create_app, db
from app.models import Student, StudentUser
from datetime import datetime


def generate_username(name, roll_number):
    """Generate username from name and roll number"""
    name_part = name.lower().replace(' ', '')[:8]
    roll_part = str(roll_number).zfill(4)
    return f"{name_part}_{roll_part}"


def create_student_accounts():
    app = create_app()
    with app.app_context():
        students = Student.query.all()
        created = 0
        updated = 0

        print("\n" + "=" * 60)
        print("📝 Creating/Updating Student Accounts")
        print("=" * 60)

        for student in students:
            existing = StudentUser.query.filter_by(student_id=student.id).first()
            username = generate_username(student.name, student.roll_number)
            password = str(student.roll_number)

            if existing:
                print(f"\n🔄 Updating account for {student.name}")
                print(f"   Username: {username}")
                existing.username = username
                existing.set_password(password)
                print(f"   Password set to: {password}")
                updated += 1
            else:
                student_user = StudentUser(
                    student_id=student.id,
                    username=username,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                student_user.set_password(password)
                db.session.add(student_user)
                created += 1

                print(f"\n✅ Created account for {student.name}")
                print(f"   Username: {username}")
                print(f"   Password: {password}")

        db.session.commit()

        print("\n" + "=" * 60)
        print(f"✅ Summary: {created} new accounts created, {updated} accounts updated")
        print("=" * 60)

        print("\n📋 Current Student Login Credentials:")
        print("-" * 60)
        for student_user in StudentUser.query.all():
            student = student_user.student
            print(f"Name: {student.name}")
            print(f"Username: {student_user.username}")
            print(f"Password: {student.roll_number}")
            print(f"Student ID: {student.student_id}")
            print("-" * 40)


if __name__ == "__main__":
    create_student_accounts()