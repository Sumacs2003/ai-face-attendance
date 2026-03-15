// Main JavaScript file

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialize all tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
});

// Face capture functionality
class FaceCapture {
    constructor(videoElement, canvasElement, captureButton) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.captureButton = captureButton;
        this.stream = null;
        this.isCapturing = false;
    }
    
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 640, 
                    height: 480,
                    facingMode: 'user'
                } 
            });
            this.video.srcObject = this.stream;
            this.isCapturing = true;
            return true;
        } catch (err) {
            console.error('Error accessing camera:', err);
            return false;
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.video.srcObject = null;
            this.isCapturing = false;
        }
    }
    
    captureImage() {
        if (!this.isCapturing) return null;
        
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        const context = this.canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // Get image data as base64
        return this.canvas.toDataURL('image/jpeg', 0.9);
    }
    
    async detectFace() {
        const imageData = this.captureImage();
        if (!imageData) return null;
        
        // Send to server for face detection
        try {
            const response = await fetch('/attendance/api/capture-face', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData })
            });
            
            return await response.json();
        } catch (err) {
            console.error('Error detecting face:', err);
            return null;
        }
    }
}

// Attendance table filtering
class AttendanceFilter {
    constructor(tableId, filterInputId) {
        this.table = document.getElementById(tableId);
        this.filterInput = document.getElementById(filterInputId);
        this.rows = this.table ? this.table.querySelectorAll('tbody tr') : [];
        
        if (this.filterInput) {
            this.filterInput.addEventListener('keyup', () => this.filter());
        }
    }
    
    filter() {
        const searchText = this.filterInput.value.toLowerCase();
        
        this.rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchText) ? '' : 'none';
        });
    }
}

// Export functionality
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td, th');
        const rowData = [];
        cells.forEach(cell => {
            rowData.push('"' + cell.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Date picker initialization
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required]');
    
    inputs.forEach(input => {
        if (!input.value) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Confirmation dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Loading spinner
function showLoading(show = true) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initDatePickers();
    
    // Add export buttons to tables
    const tables = document.querySelectorAll('.table');
    tables.forEach((table, index) => {
        if (table.id) {
            const exportBtn = document.createElement('button');
            exportBtn.className = 'btn btn-sm btn-success mb-2';
            exportBtn.innerHTML = '<i class="fas fa-download"></i> Export to CSV';
            exportBtn.onclick = () => exportTableToCSV(table.id, `export_${index}.csv`);
            table.parentNode.insertBefore(exportBtn, table);
        }
    });
});