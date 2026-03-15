# Face Attendance System - Project Setup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Face Attendance System Setup Script  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Python installed: $pythonVersion" -ForegroundColor Green

# Check Python version
$versionMatch = [regex]::Match($pythonVersion, 'Python (\d+)\.(\d+)')
if ($versionMatch.Success) {
    $major = [int]$versionMatch.Groups[1].Value
    $minor = [int]$versionMatch.Groups[2].Value
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Host "WARNING: Python 3.8 or higher is recommended. You have $major.$minor" -ForegroundColor Yellow
    }
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Yellow
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not activate virtual environment. Continuing anyway..." -ForegroundColor Yellow
}

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Some dependencies may have failed. Check the errors above." -ForegroundColor Yellow
    } else {
        Write-Host "OK: Dependencies installed successfully" -ForegroundColor Green
    }
} else {
    Write-Host "ERROR: requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host ""
Write-Host "Creating project directories..." -ForegroundColor Yellow
$directories = @(
    "app\face_data",
    "app\static\uploads",
    "app\static\css",
    "app\static\js",
    "app\static\images",
    "database"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir"
    }
}
Write-Host "OK: Directories created" -ForegroundColor Green

# Initialize database
Write-Host ""
Write-Host "Initializing database with sample data..." -ForegroundColor Yellow
python init_db.py

# Check if .env exists
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "No .env file found. Creating default..." -ForegroundColor Yellow
    $envContent = @"
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///E:\face-attendance-system\pythonProject\database\attendance.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
TEACHER_USERNAME=teacher
TEACHER_PASSWORD=teacher123
TEACHER_EMAIL=teacher@example.com
"@
    $envContent | Out-File -FilePath ".env" -Encoding ASCII
    Write-Host "OK: Created default .env file" -ForegroundColor Green
    Write-Host "Please review and update .env with your configuration if needed." -ForegroundColor Yellow
} else {
    Write-Host "OK: .env file already exists" -ForegroundColor Green
}

# Final message
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "        SETUP COMPLETE!        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor White
Write-Host " 1. Activate virtual environment: .\.venv\Scripts\activate" -ForegroundColor Yellow
Write-Host " 2. Run the application: python run.py" -ForegroundColor Yellow
Write-Host " 3. Open your browser to: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "LOGIN CREDENTIALS:" -ForegroundColor White
Write-Host "   Admin  -> Username: admin  | Password: admin123"
Write-Host "   Teacher -> Username: teacher | Password: teacher123"
Write-Host ""
Write-Host "PROJECT STRUCTURE:" -ForegroundColor White
Write-Host "   app/              # Application code"
Write-Host "   database/         # Database files"
Write-Host "   .venv/            # Virtual environment"
Write-Host "   requirements.txt  # Dependencies"
Write-Host "   .env              # Environment variables"
Write-Host "   run.py            # Application entry point"
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  System ready! Happy coding!  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan