from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError, NumberRange
import re

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters")])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('new_password', message="Passwords must match")])
    submit = SubmitField('Change Password')

def validate_phone(form, field):
    """Custom validator for phone numbers"""
    if field.data:
        phone = re.sub(r'\D', '', field.data)
        if len(phone) != 10:
            raise ValidationError('Phone number must be 10 digits')
        if not phone.isdigit():
            raise ValidationError('Phone number must contain only digits')

class StudentForm(FlaskForm):
    """Student registration form"""
    student_id = StringField('Student ID', validators=[Optional(), Length(max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(max=20)])
    class_name = StringField('Class', validators=[Optional(), Length(max=50)])
    section = StringField('Section', validators=[Optional(), Length(max=10)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20), validate_phone])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Student')

class DateRangeForm(FlaskForm):
    """Date range form for reports"""
    from_date = StringField('From Date', validators=[DataRequired()])
    to_date = StringField('To Date', validators=[DataRequired()])
    class_filter = SelectField('Class', choices=[], validators=[Optional()])
    submit = SubmitField('Generate Report')

class SystemSettingsForm(FlaskForm):
    """System settings form"""
    site_name = StringField('Site Name', validators=[Optional(), Length(max=100)])
    items_per_page = IntegerField('Items Per Page', validators=[Optional(), NumberRange(min=5, max=100)])
    attendance_threshold = FloatField('Face Recognition Threshold',
                                     validators=[Optional(), NumberRange(min=0.1, max=1.0)])
    auto_refresh_interval = IntegerField('Auto Refresh Interval (seconds)',
                                        validators=[Optional(), NumberRange(min=5, max=300)])
    session_timeout = IntegerField('Session Timeout (minutes)',
                                  validators=[Optional(), NumberRange(min=5, max=1440)])
    max_login_attempts = IntegerField('Max Login Attempts',
                                     validators=[Optional(), NumberRange(min=1, max=10)])
    submit = SubmitField('Save Settings')

class LeaveRequestForm(FlaskForm):
    """Leave request form for students"""
    from_date = StringField('From Date', validators=[DataRequired()])
    to_date = StringField('To Date', validators=[DataRequired()])
    reason = TextAreaField('Reason for Leave', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Submit Request')

class DatabaseBackupForm(FlaskForm):
    """Database backup form"""
    backup_name = StringField('Backup Name', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Create Backup')