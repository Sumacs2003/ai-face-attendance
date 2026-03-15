#!/usr/bin/env python
"""
Student Account Creation Script
Run this script to create or update student login accounts.
Usage: python create_student_accounts.py
"""

import sys
import os
from datetime import datetime

# Add the parent directory to path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Student, StudentUser


def generate_username(name, roll_number):
    """
    Generate a username from student name and roll number

    Format: {firstname}_{roll_number_padded_to_4_digits}
    Example: john_0001, jane_0002

    Args:
        name (str): Student's full name
        roll_number (str/int): Student's roll number

    Returns:
        str: Generated username
    """
    # Take first 8 characters of name, convert to lowercase, remove spaces
    name_part = name.lower().replace(' ', '')[:8]

    # Convert roll number to string and pad with zeros to 4 digits
    roll_part = str(roll_number).zfill(4)

    return f"{name_part}_{roll_part}"


def create_student_accounts():
    """
    Main function to create or update student login accounts
    """
    print("\n" + "=" * 70)
    print("🎓 FACE ATTENDANCE SYSTEM - STUDENT ACCOUNT MANAGER")
    print("=" * 70)

    # Create app context
    app = create_app()

    with app.app_context():
        # Get all students from database
        students = Student.query.all()

        if not students:
            print("\n❌ No students found in the database.")
            print("   Please add students first using the admin panel.")
            return

        print(f"\n📊 Found {len(students)} students in database")
        print("-" * 70)

        # Statistics counters
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for student in students:
            print(f"\n▶ Processing: {student.name}")
            print(f"   ID: {student.student_id}, Roll: {student.roll_number}")

            # Check if account already exists
            existing = StudentUser.query.filter_by(student_id=student.id).first()

            # Generate username and password
            username = generate_username(student.name, student.roll_number)
            password = str(student.roll_number)

            if existing:
                # Update existing account
                print(f"   🔄 Account exists - Updating...")
                old_username = existing.username
                existing.username = username
                existing.set_password(password)
                existing.is_active = True
                print(f"   ✅ Updated: {old_username} → {username}")
                print(f"   🔑 Password: {password}")
                updated_count += 1
            else:
                # Create new account
                print(f"   ✨ Creating new account...")
                student_user = StudentUser(
                    student_id=student.id,
                    username=username,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                student_user.set_password(password)
                db.session.add(student_user)
                print(f"   ✅ Created: {username}")
                print(f"   🔑 Password: {password}")
                created_count += 1

            # Commit after each student to ensure progress is saved
            db.session.commit()

        print("\n" + "=" * 70)
        print("📋 SUMMARY REPORT")
        print("=" * 70)
        print(f"   ✅ New accounts created: {created_count}")
        print(f"   🔄 Existing accounts updated: {updated_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   📊 Total students processed: {len(students)}")
        print("-" * 70)

        # Display all student credentials
        print("\n🔑 STUDENT LOGIN CREDENTIALS")
        print("=" * 70)
        print(f"{'Name':<20} {'Username':<20} {'Password':<10} {'Student ID':<15}")
        print("-" * 70)

        for student_user in StudentUser.query.order_by(StudentUser.username).all():
            student = student_user.student
            print(f"{student.name:<20} {student_user.username:<20} {student.roll_number:<10} {student.student_id:<15}")

        print("=" * 70)
        print("\n✅ Student account creation completed successfully!")
        print("\n🌐 Login URL: http://127.0.0.1:5001/auth/student-login")
        print("=" * 70)


def delete_all_student_accounts():
    """
    Utility function to delete all student accounts
    Use with caution!
    """
    print("\n" + "=" * 70)
    print("⚠️  DANGER ZONE - DELETE ALL STUDENT ACCOUNTS")
    print("=" * 70)

    confirm = input("Are you sure you want to delete ALL student accounts? (yes/no): ")

    if confirm.lower() == 'yes':
        app = create_app()
        with app.app_context():
            count = StudentUser.query.delete()
            db.session.commit()
            print(f"✅ Deleted {count} student accounts")
    else:
        print("❌ Operation cancelled")


def show_all_accounts():
    """
    Display all student accounts without modifying them
    """
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("📋 CURRENT STUDENT ACCOUNTS")
        print("=" * 70)
        print(f"{'Name':<20} {'Username':<20} {'Password':<10} {'Student ID':<15} {'Status':<10}")
        print("-" * 70)

        for student_user in StudentUser.query.order_by(StudentUser.username).all():
            student = student_user.student
            status = "Active" if student_user.is_active else "Inactive"
            print(
                f"{student.name:<20} {student_user.username:<20} {student.roll_number:<10} {student.student_id:<15} {status:<10}")

        print("=" * 70)
        print(f"Total accounts: {StudentUser.query.count()}")


def fix_passwords():
    """
    Reset all student passwords to their roll numbers
    """
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("🔧 FIXING STUDENT PASSWORDS")
        print("=" * 70)

        fixed_count = 0
        for student_user in StudentUser.query.all():
            student = student_user.student
            password = str(student.roll_number)
            student_user.set_password(password)
            fixed_count += 1
            print(f"✅ Fixed: {student_user.username} → Password: {password}")

        db.session.commit()
        print(f"\n✅ Fixed {fixed_count} passwords")


if __name__ == "__main__":
    """
    Main execution - Parse command line arguments
    """
    import argparse

    parser = argparse.ArgumentParser(description='Manage student login accounts')
    parser.add_argument('--action', type=str, default='create',
                        choices=['create', 'show', 'delete', 'fix'],
                        help='Action to perform (default: create)')

    args = parser.parse_args()

    if args.action == 'create':
        create_student_accounts()
    elif args.action == 'show':
        show_all_accounts()
    elif args.action == 'delete':
        delete_all_student_accounts()
    elif args.action == 'fix':
        fix_passwords()