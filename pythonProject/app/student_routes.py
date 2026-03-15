from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, logout_user
from app import db
from app.models import Student, Attendance, LeaveRequest, FaceEncoding
from datetime import datetime, date, timedelta
from functools import wraps
import qrcode
from io import BytesIO
import base64
import face_recognition
import numpy as np
import json
import logging
import cv2

# Create student blueprint
student_bp = Blueprint('student', __name__, url_prefix='/student')

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# Student access decorator with better error handling
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.student_login'))

        # Check if current_user has student attribute
        if not hasattr(current_user, 'student'):
            flash('Access denied. Student privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))

        # Check if the student still exists in database
        if current_user.student is None:
            flash('Your student account no longer exists.', 'danger')
            logout_user()
            return redirect(url_for('auth.student_login'))

        return f(*args, **kwargs)

    return decorated_function


# Debug route to check student login status
@student_bp.route('/debug')
@login_required
@student_required
def debug():
    """Debug route to check student login status"""
    student = current_user.student
    return jsonify({
        'id': student.id,
        'name': student.name,
        'student_id': student.student_id,
        'roll_number': student.roll_number,
        'username': current_user.username,
        'authenticated': current_user.is_authenticated
    })


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Student dashboard"""
    student = current_user.student
    today = date.today()

    # Today's attendance
    today_attendance = Attendance.query.filter_by(
        student_id=student.id, date=today
    ).first()

    # Monthly stats
    month_start = date(today.year, today.month, 1)
    month_attendance = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= month_start,
        Attendance.date <= today
    ).all()

    present_count = sum(1 for a in month_attendance if a.status == 'present')
    absent_count = sum(1 for a in month_attendance if a.status == 'absent')
    late_count = sum(1 for a in month_attendance if a.status == 'late')

    # Last 30 days trend
    last_30_days = []
    attendance_trend = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        att = Attendance.query.filter_by(student_id=student.id, date=day).first()
        last_30_days.append(day.strftime('%d %b'))
        attendance_trend.append(1 if att and att.status == 'present' else 0)

    # Overall percentage
    total_days = (today - student.admission_date).days if student.admission_date else 30
    total_days = max(total_days, 1)
    total_attendance = Attendance.query.filter_by(student_id=student.id).count()
    attendance_percentage = (total_attendance / total_days * 100)

    # Pending leaves
    pending_leaves = LeaveRequest.query.filter_by(
        student_id=student.id, status='pending'
    ).count()

    stats = {
        'total_attendance': total_attendance,
        'attendance_percentage': round(attendance_percentage, 2),
        'present_this_month': present_count,
        'absent_this_month': absent_count,
        'late_this_month': late_count,
        'pending_leaves': pending_leaves,
        'last_30_days': last_30_days,
        'attendance_trend': attendance_trend,
        'today_status': today_attendance.status if today_attendance else 'not_marked',
        'total_days': total_days
    }

    return render_template('student/dashboard.html', student=student, stats=stats, datetime=datetime)


@student_bp.route('/attendance')
@login_required
@student_required
def attendance():
    """View own attendance"""
    student = current_user.student
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    year, month_num = map(int, month.split('-'))

    start_date = date(year, month_num, 1)
    if month_num == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month_num + 1, 1) - timedelta(days=1)

    records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()

    present = sum(1 for r in records if r.status == 'present')
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')
    total_days = (end_date - start_date).days + 1

    stats = {
        'present': present,
        'absent': absent,
        'late': late,
        'total_days': total_days,
        'percentage': round((present / total_days * 100) if total_days > 0 else 0, 2)
    }

    return render_template('student/attendance.html',
                           attendance=records,
                           stats=stats,
                           selected_month=month,
                           student=student,
                           datetime=datetime)


@student_bp.route('/face-attendance', methods=['GET', 'POST'])
@login_required
@student_required
def face_attendance():
    """Face recognition attendance for students"""
    student = current_user.student
    today = date.today()

    # Check if already marked today
    today_attendance = Attendance.query.filter_by(
        student_id=student.id, date=today
    ).first()

    if request.method == 'POST':
        try:
            data = request.get_json()
            image_data = data.get('image')

            if not image_data:
                return jsonify({'success': False, 'message': 'No image provided'})

            # Decode base64 image
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Get face encoding from the captured image
            face_locations = face_recognition.face_locations(rgb_img)

            if not face_locations:
                return jsonify({'success': False, 'message': 'No face detected. Please try again.'})

            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

            if not face_encodings:
                return jsonify({'success': False, 'message': 'Could not encode face. Please try again.'})

            # Get the student's stored face encoding
            stored_encoding = FaceEncoding.query.filter_by(student_id=student.id).first()

            if not stored_encoding:
                return jsonify({'success': False, 'message': 'No face registered for you. Please contact admin.'})

            # Compare faces
            known_encoding = np.array(json.loads(stored_encoding.encoding))
            match = face_recognition.compare_faces([known_encoding], face_encodings[0])[0]

            if match:
                distance = face_recognition.face_distance([known_encoding], face_encodings[0])[0]
                confidence = 1 - distance

                if confidence > 0.5:  # Threshold
                    # Mark attendance
                    if today_attendance:
                        return jsonify({'success': False, 'message': 'Attendance already marked for today!'})

                    attendance = Attendance(
                        student_id=student.id,
                        date=today,
                        timestamp=datetime.now(),
                        status='present',
                        confidence=float(confidence),
                        remarks='Marked via student self-service'
                    )
                    db.session.add(attendance)
                    db.session.commit()

                    return jsonify({
                        'success': True,
                        'message': 'Attendance marked successfully!',
                        'confidence': float(confidence)
                    })
                else:
                    return jsonify(
                        {'success': False, 'message': f'Confidence too low: {confidence:.2f}. Please try again.'})
            else:
                return jsonify({'success': False, 'message': 'Face does not match. Please try again.'})

        except Exception as e:
            logging.error(f"Error in face attendance: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})

    return render_template('student/face_attendance.html',
                           student=student,
                           today_attendance=today_attendance,
                           datetime=datetime)


@student_bp.route('/leave-request', methods=['GET', 'POST'])
@login_required
@student_required
def leave_request():
    """Request leave"""
    student = current_user.student

    if request.method == 'POST':
        from_date = datetime.strptime(request.form['from_date'], '%Y-%m-%d').date()
        to_date = datetime.strptime(request.form['to_date'], '%Y-%m-%d').date()
        reason = request.form['reason']

        if from_date > to_date:
            flash('From date cannot be after to date!', 'danger')
            return redirect(url_for('student.leave_request'))

        if from_date < date.today():
            flash('Cannot request leave for past dates!', 'danger')
            return redirect(url_for('student.leave_request'))

        existing = LeaveRequest.query.filter(
            LeaveRequest.student_id == student.id,
            LeaveRequest.status.in_(['pending', 'approved']),
            LeaveRequest.from_date <= to_date,
            LeaveRequest.to_date >= from_date
        ).first()

        if existing:
            flash('You already have a pending or approved leave request for this period!', 'danger')
            return redirect(url_for('student.leave_request'))

        leave = LeaveRequest(
            student_id=student.id,
            from_date=from_date,
            to_date=to_date,
            reason=reason
        )
        db.session.add(leave)
        db.session.commit()

        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('student.leave_history'))

    return render_template('student/leave_request.html', student=student, datetime=datetime)


@student_bp.route('/leave-history')
@login_required
@student_required
def leave_history():
    """View leave history"""
    student = current_user.student
    leaves = LeaveRequest.query.filter_by(student_id=student.id) \
        .order_by(LeaveRequest.requested_on.desc()).all()

    total_leaves = len(leaves)
    pending = sum(1 for l in leaves if l.status == 'pending')
    approved = sum(1 for l in leaves if l.status == 'approved')
    rejected = sum(1 for l in leaves if l.status == 'rejected')

    stats = {
        'total': total_leaves,
        'pending': pending,
        'approved': approved,
        'rejected': rejected
    }

    return render_template('student/leave_history.html', leaves=leaves, stats=stats)


@student_bp.route('/qr-code')
@login_required
@student_required
def qr_code():
    """Generate QR code for student"""
    student = current_user.student

    qr_data = f"""STUDENT QR CODE
Name: {student.name}
ID: {student.student_id}
Roll: {student.roll_number}
Class: {student.class_name} {student.section}
"""

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
        error_correction=qrcode.constants.ERROR_CORRECT_L
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()

    return render_template('student/qr_code.html', student=student, qr_code=qr_code)


@student_bp.route('/profile')
@login_required
@student_required
def profile():
    """View profile"""
    student = current_user.student

    today = date.today()
    total_days = (today - student.admission_date).days if student.admission_date else 30
    total_days = max(total_days, 1)
    total_attendance = Attendance.query.filter_by(student_id=student.id).count()
    attendance_percentage = (total_attendance / total_days * 100)

    month_start = date(today.year, today.month, 1)
    month_attendance = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= month_start,
        Attendance.date <= today
    ).all()

    stats = {
        'total_attendance': total_attendance,
        'attendance_percentage': round(attendance_percentage, 2),
        'present_this_month': sum(1 for a in month_attendance if a.status == 'present'),
        'absent_this_month': sum(1 for a in month_attendance if a.status == 'absent'),
        'late_this_month': sum(1 for a in month_attendance if a.status == 'late'),
        'total_days': total_days
    }

    return render_template('student/profile.html', student=student, stats=stats, datetime=datetime)


@student_bp.route('/change-password', methods=['POST'])
@login_required
@student_required
def change_password():
    """Change student password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('student.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('student.profile'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'danger')
        return redirect(url_for('student.profile'))

    current_user.set_password(new_password)
    db.session.commit()

    flash('Password changed successfully!', 'success')
    return redirect(url_for('student.profile'))


@student_bp.route('/api/stats')
@login_required
@student_required
def api_stats():
    """API for student statistics"""
    student = current_user.student
    today = date.today()

    week_start = today - timedelta(days=today.weekday())
    week_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        att = Attendance.query.filter_by(student_id=student.id, date=day).first()
        week_data.append({
            'date': day.strftime('%A'),
            'status': att.status if att else 'not_marked'
        })

    month_data = []
    for i in range(1, 13):
        month_start = date(today.year, i, 1)
        if i == 12:
            month_end = date(today.year, 12, 31)
        else:
            month_end = date(today.year, i + 1, 1) - timedelta(days=1)

        count = Attendance.query.filter(
            Attendance.student_id == student.id,
            Attendance.date >= month_start,
            Attendance.date <= month_end,
            Attendance.status == 'present'
        ).count()

        month_data.append({
            'month': month_start.strftime('%B'),
            'count': count
        })

    return jsonify({
        'week_data': week_data,
        'month_data': month_data
    })


@student_bp.route('/cancel-leave/<int:id>', methods=['POST'])
@login_required
@student_required
def cancel_leave(id):
    """Cancel a pending leave request"""
    leave = LeaveRequest.query.get_or_404(id)

    if leave.student_id != current_user.student.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    if leave.status != 'pending':
        return jsonify({'success': False, 'message': 'Only pending requests can be cancelled'})

    db.session.delete(leave)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Leave request cancelled'})


# Error handlers
@student_bp.errorhandler(404)
def not_found_error(error):
    return render_template('student/404.html'), 404


@student_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('student/500.html'), 500