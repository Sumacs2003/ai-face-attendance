# setup_complete.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Face Attendance System - Complete Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Create necessary directories
Write-Host "`n[1/4] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "app\static\uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "app\static\faces" | Out-Null
New-Item -ItemType Directory -Force -Path "app\static\captured_faces" | Out-Null
New-Item -ItemType Directory -Force -Path "database" | Out-Null
New-Item -ItemType Directory -Force -Path "templates" | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green

# Step 2: Reset database
Write-Host "`n[2/4] Resetting database..." -ForegroundColor Yellow
python reset_db.py

# Step 3: Check if templates exist
Write-Host "`n[3/4] Checking template files..." -ForegroundColor Yellow
$required_templates = @(
    "login.html",
    "dashboard.html",
    "register_face_select.html",
    "register_face.html",
    "capture_face.html",
    "student_list.html",
    "add_student.html",
    "take_attendance.html",
    "view_attendance.html"
)

$missing_templates = @()
foreach ($template in $required_templates) {
    if (-not (Test-Path "templates\$template")) {
        $missing_templates += $template
    }
}

if ($missing_templates.Count -gt 0) {
    Write-Host "⚠️  Missing templates: $($missing_templates -join ', ')" -ForegroundColor Yellow
    Write-Host "   Please add these template files to the templates folder." -ForegroundColor Yellow
} else {
    Write-Host "✅ All required templates found" -ForegroundColor Green
}

# Step 4: Start the application
Write-Host "`n[4/4] Starting application..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Application will start at: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Login: admin / admin123" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

python run.py