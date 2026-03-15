from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import db, csrf
from app.models import User, Student, Attendance, FaceEncoding, Class, Settings, StudentUser, LeaveRequest
from app.forms import LoginForm, ChangePasswordForm, StudentForm, SystemSettingsForm
from datetime import datetime, date, timedelta
import os
import json
import base64
import numpy as np
from werkzeug.utils import secure_filename
import face_recognition
from sqlalchemy import func
from functools import wraps
import cv2
import logging
import sys
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)
staff_bp = Blueprint('staff', __name__, url_prefix='/staff')
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')
face_bp = Blueprint('face', __name__, url_prefix='/face')


# ==================== DECORATORS ====================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def teacher_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


def can_add_student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.can_add_student():
            flash('You do not have permission to add students.', 'danger')
            return redirect(url_for('staff.list'))
        return f(*args, **kwargs)

    return decorated_function


# ==================== AUTH ROUTES ====================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if hasattr(current_user, 'student'):
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account is deactivated.', 'danger')
                return render_template('login.html', form=form)
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/student-login', methods=['GET', 'POST'])
def student_login():
    """Student login page - FIXED VERSION"""
    if current_user.is_authenticated:
        if hasattr(current_user, 'student'):
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Debug logging
        app = current_app._get_current_object()
        app.logger.info(f"Student login attempt - Username: {username}")

        # Find the student user
        student_user = StudentUser.query.filter_by(username=username).first()

        if student_user:
            app.logger.info(f"Student found: {student_user.username}")
            # Use check_password method to verify
            if student_user.check_password(password):
                app.logger.info("Password check passed!")
                if not student_user.is_active:
                    flash('Your account is deactivated.', 'danger')
                    return render_template('student_login.html')
                login_user(student_user, remember=True)
                student_user.last_login = datetime.utcnow()
                db.session.commit()
                flash(f'Welcome back, {student_user.student.name}!', 'success')
                return redirect(url_for('student.dashboard'))
            else:
                app.logger.info("Password check failed!")
                flash('Invalid username or password', 'danger')
        else:
            app.logger.info(f"No student found with username: {username}")
            flash('Invalid username or password', 'danger')

    return render_template('student_login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    form = ChangePasswordForm()
    return render_template('profile.html', form=form, datetime=datetime)


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
        else:
            flash('Current password is incorrect', 'danger')
    return redirect(url_for('auth.profile'))


# ==================== MAIN ROUTES ====================

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if hasattr(current_user, 'student'):
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    total_students = Student.query.count()

    if current_user.is_admin or current_user.is_teacher:
        try:
            total_classes = Class.query.count()
            today_attendance = db.session.query(Attendance.student_id).filter(
                Attendance.date == today).distinct().count()
        except:
            total_classes = 0
            today_attendance = 0

        last_30_days = []
        attendance_trend = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            try:
                count = db.session.query(Attendance.student_id).filter(
                    Attendance.date == day).distinct().count()
            except:
                count = 0
            last_30_days.append(day.strftime('%d %b'))
            attendance_trend.append(count)

        recent_attendance = Attendance.query.order_by(Attendance.timestamp.desc()).limit(10).all()
        class_attendance = db.session.query(Student.class_name, func.count(Attendance.id)).join(Attendance).filter(
            Attendance.date == today).group_by(Student.class_name).all()
    else:
        total_classes = 0
        today_attendance = 0
        last_30_days = []
        attendance_trend = []
        recent_attendance = []
        class_attendance = []

    present_percentage = (today_attendance / total_students * 100) if total_students > 0 else 0

    stats = {
        'total_students': total_students,
        'total_classes': total_classes,
        'today_attendance': today_attendance,
        'present_percentage': round(present_percentage, 2),
        'absent_today': total_students - today_attendance,
        'last_30_days': last_30_days,
        'attendance_trend': attendance_trend,
        'recent_attendance': recent_attendance,
        'class_attendance': class_attendance,
        'current_date': today.strftime('%A, %B %d, %Y'),
        'is_admin': current_user.is_admin
    }
    return render_template('dashboard.html', stats=stats, datetime=datetime)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """System settings page"""
    form = SystemSettingsForm()

    # Load existing settings
    settings_dict = {}
    try:
        all_settings = Settings.query.all()
        for setting in all_settings:
            settings_dict[setting.key] = setting.value
    except:
        pass

    if request.method == 'GET':
        form.site_name.data = settings_dict.get('site_name', 'Face Attendance System')
        form.items_per_page.data = int(settings_dict.get('items_per_page', 10))
        form.attendance_threshold.data = float(settings_dict.get('attendance_threshold', 0.6))
        form.auto_refresh_interval.data = int(settings_dict.get('auto_refresh_interval', 30))
        form.session_timeout.data = int(settings_dict.get('session_timeout', 30))
        form.max_login_attempts.data = int(settings_dict.get('max_login_attempts', 5))

    if form.validate_on_submit():
        try:
            settings_to_save = {
                'site_name': form.site_name.data,
                'items_per_page': str(form.items_per_page.data),
                'attendance_threshold': str(form.attendance_threshold.data),
                'auto_refresh_interval': str(form.auto_refresh_interval.data),
                'session_timeout': str(form.session_timeout.data),
                'max_login_attempts': str(form.max_login_attempts.data)
            }

            for key, value in settings_to_save.items():
                setting = Settings.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = Settings(key=key, value=value, description=f'System setting: {key}')
                    db.session.add(setting)

            db.session.commit()
            flash('Settings saved successfully!', 'success')
            return redirect(url_for('main.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving settings: {str(e)}', 'danger')

    return render_template('settings.html', form=form, now=datetime.now)


# ==================== DATABASE MANAGEMENT ROUTES ====================

@main_bp.route('/database/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def database_manage():
    """Database management page"""
    from database_manager import DatabaseManager
    db_manager = DatabaseManager()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'backup':
            try:
                backup_path = db_manager.backup_database()
                flash(f'✅ Database backup created successfully at: {os.path.basename(backup_path)}', 'success')
            except Exception as e:
                flash(f'❌ Error creating backup: {str(e)}', 'danger')

        elif action == 'restore':
            backup_file = request.files.get('backup_file')
            if backup_file and backup_file.filename.endswith('.db'):
                try:
                    os.makedirs('database/temp', exist_ok=True)
                    temp_path = f'database/temp/restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                    backup_file.save(temp_path)

                    if db_manager.restore_database(temp_path):
                        flash('✅ Database restored successfully!', 'success')
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        return redirect(url_for('main.dashboard'))
                    else:
                        flash('❌ Failed to restore database. The backup file might be corrupted.', 'danger')
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                except Exception as e:
                    flash(f'❌ Error during restore: {str(e)}', 'danger')
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                flash('❌ Please upload a valid .db file', 'danger')

        elif action == 'optimize':
            try:
                db_manager.optimize_database()
                flash('✅ Database optimized successfully!', 'success')
            except Exception as e:
                flash(f'❌ Error optimizing database: {str(e)}', 'danger')

        elif action == 'export':
            try:
                exported_files = db_manager.export_to_json()
                if exported_files:
                    flash(f'✅ Exported {len(exported_files)} tables to JSON', 'success')
                else:
                    flash('❌ No data to export or export failed', 'danger')
            except Exception as e:
                flash(f'❌ Error exporting data: {str(e)}', 'danger')

        elif action == 'cleanup':
            try:
                keep_days = int(request.form.get('keep_days', 7))
                removed = db_manager.cleanup_old_backups(keep_days)
                if removed > 0:
                    flash(f'✅ Removed {removed} old backup(s) older than {keep_days} days', 'success')
                else:
                    flash(f'ℹ️ No backups older than {keep_days} days found', 'info')
            except Exception as e:
                flash(f'❌ Error during cleanup: {str(e)}', 'danger')

    try:
        stats = db_manager.get_database_stats()
    except Exception as e:
        stats = {'size_mb': 0, 'tables': {}, 'last_modified': 'Error loading stats'}
        flash(f'⚠️ Warning: Could not load database stats: {str(e)}', 'warning')

    try:
        backups = db_manager.list_backups()
    except Exception as e:
        backups = []
        flash(f'⚠️ Warning: Could not list backups: {str(e)}', 'warning')

    return render_template('database_manage.html', stats=stats, backups=backups)


@main_bp.route('/database/download/<filename>')
@login_required
@admin_required
def download_backup(filename):
    """Download a backup file"""
    if '..' in filename or '/' in filename or '\\' in filename:
        flash('❌ Invalid filename', 'danger')
        return redirect(url_for('main.database_manage'))

    backup_path = f'database/backups/{filename}'
    if os.path.exists(backup_path):
        try:
            return send_file(
                backup_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )
        except Exception as e:
            flash(f'❌ Error downloading file: {str(e)}', 'danger')
    else:
        flash('❌ Backup file not found', 'danger')

    return redirect(url_for('main.database_manage'))


# ==================== STAFF MANAGEMENT ROUTES ====================

@staff_bp.route('/list')
@login_required
@teacher_or_admin_required
def list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    class_filter = request.args.get('class', '')

    query = Student.query
    if search:
        query = query.filter(db.or_(
            Student.name.ilike(f'%{search}%'),
            Student.roll_number.ilike(f'%{search}%'),
            Student.student_id.ilike(f'%{search}%')
        ))
    if class_filter:
        query = query.filter(Student.class_name == class_filter)

    students = query.order_by(Student.name).paginate(page=page, per_page=per_page)
    classes = db.session.query(Student.class_name).distinct().all()
    classes = [c[0] for c in classes if c[0]]

    return render_template('student_list.html', students=students, classes=classes, is_admin=current_user.is_admin)


# ==================== FIXED ADD STUDENT ROUTE WITH AUTO LOGIN CREATION ====================
@staff_bp.route('/add', methods=['GET', 'POST'])
@login_required
@can_add_student_required
def add():
    form = StudentForm()
    if form.validate_on_submit():
        try:
            if not form.student_id.data:
                last_student = Student.query.order_by(Student.id.desc()).first()
                if last_student and last_student.student_id:
                    try:
                        last_num = int(last_student.student_id.split('-')[-1])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
                student_id = f"STU-{str(new_num).zfill(4)}"
            else:
                student_id = form.student_id.data

            # Create the student
            student = Student(
                student_id=student_id,
                name=form.name.data,
                roll_number=form.roll_number.data,
                class_name=form.class_name.data,
                section=form.section.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                admission_date=datetime.utcnow().date()
            )
            db.session.add(student)
            db.session.flush()  # This assigns an ID to the student

            # AUTO-CREATE LOGIN ACCOUNT FOR THE STUDENT - FIXED VERSION
            name_part = student.name.lower().replace(' ', '')[:8]
            # CRITICAL: Convert roll_number to string properly
            roll_str = str(student.roll_number).strip()
            roll_part = roll_str.zfill(4)
            username = f"{name_part}_{roll_part}"
            password = roll_str  # Password is the roll number as string

            # Check if username already exists (unlikely but handle it)
            existing_user = StudentUser.query.filter_by(username=username).first()
            if existing_user:
                # Add a random suffix to make it unique
                suffix = random.randint(100, 999)
                username = f"{name_part}_{roll_part}_{suffix}"

            student_user = StudentUser(
                student_id=student.id,
                username=username,
                is_active=True
            )
            # CRITICAL: Use set_password method, not direct assignment
            student_user.set_password(password)
            db.session.add(student_user)

            db.session.commit()

            flash(f'✅ Student {student.name} added successfully!', 'success')
            flash(f'🔑 Login: Username: {username}, Password: {password}', 'info')
            return redirect(url_for('staff.list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'danger')
    return render_template('add_student.html', form=form, is_admin=current_user.is_admin)


@staff_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@can_add_student_required
def edit(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)

    if form.validate_on_submit():
        try:
            student.name = form.name.data
            student.roll_number = form.roll_number.data
            student.class_name = form.class_name.data
            student.section = form.section.data
            student.email = form.email.data
            student.phone = form.phone.data
            student.address = form.address.data
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('staff.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'danger')
    return render_template('edit_student.html', form=form, student=student, is_admin=current_user.is_admin)


@staff_bp.route('/view/<int:id>')
@login_required
@teacher_or_admin_required
def view(id):
    student = Student.query.get_or_404(id)
    attendance_records = Attendance.query.filter_by(student_id=id).order_by(Attendance.date.desc()).limit(30).all()
    has_account = StudentUser.query.filter_by(student_id=id).first() is not None
    return render_template('view_student.html', student=student, attendance=attendance_records,
                           is_admin=current_user.is_admin, datetime=datetime, has_account=has_account)


@staff_bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete(id):
    student = Student.query.get_or_404(id)
    try:
        student_user = StudentUser.query.filter_by(student_id=id).first()
        if student_user:
            db.session.delete(student_user)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student.name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'danger')
    return redirect(url_for('staff.list'))


@staff_bp.route('/create-login/<int:id>', methods=['POST'])
@login_required
@admin_required
def create_login(id):
    """Create login account for student"""
    student = Student.query.get_or_404(id)

    existing = StudentUser.query.filter_by(student_id=id).first()
    if existing:
        flash(f'Login account already exists for {student.name}', 'warning')
        return redirect(url_for('staff.view', id=id))

    name_part = student.name.lower().replace(' ', '')[:8]
    roll_str = str(student.roll_number).strip()
    roll_part = roll_str.zfill(4)
    username = f"{name_part}_{roll_part}"
    password = roll_str

    student_user = StudentUser(
        student_id=id,
        username=username,
        is_active=True
    )
    student_user.set_password(password)

    db.session.add(student_user)
    db.session.commit()

    flash(f'✅ Login account created for {student.name}. Username: {username}, Password: {password}', 'success')
    return redirect(url_for('staff.view', id=id))


@staff_bp.route('/reset-password/<int:id>', methods=['POST'])
@login_required
@admin_required
def reset_password(id):
    """Reset student password to default (roll number)"""
    student = Student.query.get_or_404(id)
    student_user = StudentUser.query.filter_by(student_id=id).first()

    if not student_user:
        flash(f'No login account found for {student.name}', 'danger')
        return redirect(url_for('staff.view', id=id))

    password = str(student.roll_number)
    student_user.set_password(password)
    db.session.commit()

    flash(f'✅ Password reset for {student.name}. New password: {password}', 'success')
    return redirect(url_for('staff.view', id=id))


# ==================== ATTENDANCE ROUTES ====================

@attendance_bp.route('/take')
@login_required
@teacher_or_admin_required
def take():
    students = Student.query.filter_by(face_encoded=True).all()
    return render_template('take_attendance.html', students=students, is_admin=current_user.is_admin, datetime=datetime)


@attendance_bp.route('/mark', methods=['POST'])
@login_required
def mark():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        confidence = data.get('confidence', 1.0)

        today = date.today()
        existing = Attendance.query.filter_by(student_id=student_id, date=today).first()
        if existing:
            return jsonify({'success': False, 'message': 'Already marked today'})

        attendance = Attendance(
            student_id=student_id,
            date=today,
            timestamp=datetime.now(),
            status='present',
            confidence=confidence,
            marked_by=current_user.id
        )
        db.session.add(attendance)
        db.session.commit()
        student = Student.query.get(student_id)
        return jsonify({'success': True, 'message': f'Attendance marked for {student.name}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@attendance_bp.route('/view')
@login_required
@teacher_or_admin_required
def view():
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    class_filter = request.args.get('class', '')

    query = Attendance.query.join(Student)
    if date_filter:
        query = query.filter(Attendance.date == date_filter)
    if class_filter:
        query = query.filter(Student.class_name == class_filter)

    attendance_records = query.order_by(Attendance.timestamp.desc()).all()
    classes = db.session.query(Student.class_name).distinct().all()
    classes = [c[0] for c in classes if c[0]]

    stats = {
        'total_present': len(attendance_records),
        'total_students': Student.query.count(),
        'percentage': round((len(attendance_records) / Student.query.count() * 100) if Student.query.count() > 0 else 0,
                            2)
    }
    return render_template('view_attendance.html', attendance=attendance_records, classes=classes,
                           selected_date=date_filter, selected_class=class_filter, stats=stats,
                           is_admin=current_user.is_admin, datetime=datetime)


@attendance_bp.route('/leave-requests')
@login_required
@teacher_or_admin_required
def leave_requests():
    """View all leave requests (Admin/Teacher)"""
    status_filter = request.args.get('status', 'pending')

    query = LeaveRequest.query.join(Student)

    if status_filter != 'all':
        query = query.filter(LeaveRequest.status == status_filter)

    leave_requests = query.order_by(LeaveRequest.requested_on.desc()).all()

    return render_template('leave_requests_admin.html',
                           leave_requests=leave_requests,
                           status_filter=status_filter)


@attendance_bp.route('/leave-request/<int:id>/<action>', methods=['POST'])
@login_required
@teacher_or_admin_required
def process_leave_request(id, action):
    """Approve or reject leave request"""
    leave_request = LeaveRequest.query.get_or_404(id)

    if action == 'approve':
        leave_request.status = 'approved'
        leave_request.processed_by = current_user.id
        leave_request.processed_on = datetime.utcnow()
        leave_request.remarks = request.json.get('remarks', 'Approved')
        flash('Leave request approved', 'success')
    elif action == 'reject':
        leave_request.status = 'rejected'
        leave_request.processed_by = current_user.id
        leave_request.processed_on = datetime.utcnow()
        leave_request.remarks = request.json.get('remarks', 'Rejected')
        flash('Leave request rejected', 'success')

    db.session.commit()
    return jsonify({'success': True})


# ==================== FACE RECOGNITION ROUTES ====================

@face_bp.route('/register/<int:student_id>')
@login_required
@admin_required
def register(student_id):
    if student_id == 0:
        students = Student.query.filter_by(face_encoded=False).all()
        return render_template('register_face_select.html', students=students, is_admin=current_user.is_admin)
    student = Student.query.get_or_404(student_id)
    return render_template('register_face.html', student=student, is_admin=current_user.is_admin)


@face_bp.route('/capture/<int:student_id>')
@login_required
@admin_required
def capture(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('capture_face.html', student=student, is_admin=current_user.is_admin)


@face_bp.route('/save-multiple-encodings', methods=['POST'])
@login_required
@admin_required
def save_multiple_encodings():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        images = data.get('images', [])

        student = Student.query.get_or_404(student_id)
        face_dir = os.path.join(current_app.root_path, 'static', 'faces', str(student_id))
        os.makedirs(face_dir, exist_ok=True)

        all_encodings = []
        for i, image_data in enumerate(images):
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                continue

            filename = f"face_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jpg"
            cv2.imwrite(os.path.join(face_dir, filename), img)

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_img)
            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

            if face_encodings:
                all_encodings.append(face_encodings[0].tolist())

        if all_encodings:
            avg_encoding = np.mean(all_encodings, axis=0).tolist()
            encoding_json = json.dumps(avg_encoding)

            existing = FaceEncoding.query.filter_by(student_id=student_id).first()
            if existing:
                existing.encoding = encoding_json
            else:
                face_encoding = FaceEncoding(student_id=student_id, encoding=encoding_json)
                db.session.add(face_encoding)

            student.face_encoded = True
            db.session.commit()
            return jsonify({'success': True, 'message': f'Saved {len(all_encodings)} encodings!'})
        return jsonify({'success': False, 'message': 'No faces detected'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@face_bp.route('/recognize', methods=['POST'])
def recognize():
    try:
        data = request.get_json()
        image_data = data.get('image')
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_img)
        if not face_locations:
            return jsonify({'success': False, 'message': 'No face detected'})

        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        if not face_encodings:
            return jsonify({'success': False, 'message': 'Could not encode face'})

        known_encodings = FaceEncoding.query.all()
        matches = []
        for encoding_record in known_encodings:
            known_encoding = np.array(json.loads(encoding_record.encoding))
            match = face_recognition.compare_faces([known_encoding], face_encodings[0])[0]
            if match:
                distance = face_recognition.face_distance([known_encoding], face_encodings[0])[0]
                confidence = 1 - distance
                if confidence > 0.5:
                    student = Student.query.get(encoding_record.student_id)
                    matches.append({
                        'student_id': student.id,
                        'name': student.name,
                        'confidence': float(confidence)
                    })

        if matches:
            matches.sort(key=lambda x: x['confidence'], reverse=True)
            return jsonify({'success': True, 'matches': matches})
        return jsonify({'success': False, 'message': 'No match found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@face_bp.route('/check-camera', methods=['GET'])
def check_camera():
    """Check if camera is accessible"""
    try:
        for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY, cv2.CAP_MSMF]:
            cap = cv2.VideoCapture(0, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return jsonify({'success': True, 'message': 'Camera is accessible'})

        return jsonify({'success': False, 'error': 'Cannot access camera'})
    except Exception as e:
        logging.error(f"Camera check error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== API ROUTES ====================

@main_bp.route('/api/students/search')
@login_required
def api_search_students():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    students = Student.query.filter(db.or_(
        Student.name.ilike(f'%{query}%'),
        Student.roll_number.ilike(f'%{query}%'),
        Student.student_id.ilike(f'%{query}%')
    )).limit(10).all()
    return jsonify([{
        'id': s.id, 'name': s.name, 'roll_number': s.roll_number,
        'student_id': s.student_id, 'face_encoded': s.face_encoded,
        'has_account': StudentUser.query.filter_by(student_id=s.id).first() is not None
    } for s in students])


# ==================== ERROR HANDLERS ====================

@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500