#!/usr/bin/env python
"""
Simple Student Account Creation Script
Run this to quickly create/update student accounts
"""

from app import create_app, db
from app.models import Student, StudentUser
from datetime import datetime


def create_accounts():
    """Create or update student login accounts"""
    app = create_app()

    with app.app_context():
        print("\n" + "=" * 50)
        print("Creating Student Login Accounts")
        print("=" * 50)

        students = Student.query.all()
        created = 0
        updated = 0

        for student in students:
            # Generate username: firstname_roll (padded to 4 digits)
            name_part = student.name.lower().replace(' ', '')[:8]
            roll_part = str(student.roll_number).zfill(4)
            username = f"{name_part}_{roll_part}"
            password = str(student.roll_number)

            # Check if account exists
            existing = StudentUser.query.filter_by(student_id=student.id).first()

            if existing:
                # Update existing account
                existing.username = username
                existing.set_password(password)
                updated += 1
                print(f"🔄 Updated: {student.name} -> {username} / {password}")
            else:
                # Create new account
                new_user = StudentUser(
                    student_id=student.id,
                    username=username,
                    is_active=True
                )
                new_user.set_password(password)
                db.session.add(new_user)
                created += 1
                print(f"✅ Created: {student.name} -> {username} / {password}")

        db.session.commit()

        print("\n" + "=" * 50)
        print(f"Summary: {created} created, {updated} updated")
        print("=" * 50)


if __name__ == "__main__":
    create_accounts()