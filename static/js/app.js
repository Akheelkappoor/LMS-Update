// static/js/app.js - JavaScript functions connected to your backend

// ===================================
// FORM BUILDER FUNCTIONS
// ===================================

function previewForm(formId) {
    fetch(`/api/forms/${formId}/preview`)
        .then(response => response.json())
        .then(data => {
            showFormPreview(data.form);
        })
        .catch(error => {
            showAlert('Error loading form preview', 'danger');
        });
}

function showFormPreview(formData) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${formData.name} - Preview</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="text-muted">${formData.description || ''}</p>
                    <div id="formPreviewContent"></div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Generate form HTML from fields
    const formHTML = generateFormHTML(formData.fields);
    document.getElementById('formPreviewContent').innerHTML = formHTML;
    
    // Show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Clean up when modal is closed
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

function generateFormHTML(fields) {
    return fields.map(field => {
        switch(field.type) {
            case 'text':
                return `
                    <div class="mb-3">
                        <label class="form-label">${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}</label>
                        <input type="text" class="form-control" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''}>
                        ${field.help_text ? `<div class="form-text">${field.help_text}</div>` : ''}
                    </div>
                `;
            case 'email':
                return `
                    <div class="mb-3">
                        <label class="form-label">${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}</label>
                        <input type="email" class="form-control" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''}>
                        ${field.help_text ? `<div class="form-text">${field.help_text}</div>` : ''}
                    </div>
                `;
            case 'select':
                const options = field.options ? field.options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('') : '';
                return `
                    <div class="mb-3">
                        <label class="form-label">${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}</label>
                        <select class="form-control" ${field.required ? 'required' : ''}>
                            <option value="">-- Select --</option>
                            ${options}
                        </select>
                        ${field.help_text ? `<div class="form-text">${field.help_text}</div>` : ''}
                    </div>
                `;
            default:
                return `<div class="mb-3"><label class="form-label">${field.label}</label><input type="text" class="form-control"></div>`;
        }
    }).join('');
}

// ===================================
// USER MANAGEMENT FUNCTIONS
// ===================================

function bulkUserAction() {
    const action = document.getElementById('bulkAction').value;
    const checkboxes = document.querySelectorAll('input[name="user_ids[]"]:checked');
    
    if (!action) {
        showAlert('Please select an action', 'warning');
        return;
    }
    
    if (checkboxes.length === 0) {
        showAlert('Please select at least one user', 'warning');
        return;
    }
    
    const userIds = Array.from(checkboxes).map(cb => cb.value);
    const userName = checkboxes.length === 1 ? checkboxes[0].dataset.userName : `${checkboxes.length} users`;
    
    if (confirm(`Are you sure you want to ${action} ${userName}?`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/users/bulk-action';
        
        // Add action input
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = action;
        form.appendChild(actionInput);
        
        // Add user IDs
        userIds.forEach(id => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'user_ids[]';
            input.value = id;
            form.appendChild(input);
        });
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrf_token';
            tokenInput.value = csrfToken.getAttribute('content');
            form.appendChild(tokenInput);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}

function resetUserPassword(userId, userName) {
    if (confirm(`Reset password for ${userName}? New credentials will be sent to their email.`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/users/${userId}/reset-password`;
        
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrf_token';
            tokenInput.value = csrfToken.getAttribute('content');
            form.appendChild(tokenInput);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}

// ===================================
// STUDENT SEARCH FUNCTIONS
// ===================================

function searchStudents(query) {
    if (query.length < 2) {
        document.getElementById('studentSearchResults').innerHTML = '';
        return;
    }
    
    fetch(`/api/students/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(students => {
            const resultsDiv = document.getElementById('studentSearchResults');
            
            if (students.length === 0) {
                resultsDiv.innerHTML = '<div class="alert alert-info">No students found</div>';
                return;
            }
            
            const html = students.map(student => `
                <div class="student-result" onclick="selectStudent(${student.id})">
                    <strong>${student.name}</strong>
                    <small class="text-muted">ID: ${student.student_id} | Grade: ${student.grade || 'N/A'}</small>
                </div>
            `).join('');
            
            resultsDiv.innerHTML = html;
        })
        .catch(error => {
            console.error('Search error:', error);
            showAlert('Search failed', 'danger');
        });
}

function selectStudent(studentId) {
    // Handle student selection (e.g., for enrollment)
    document.getElementById('selectedStudentId').value = studentId;
    document.getElementById('studentSearchResults').innerHTML = '';
    document.getElementById('studentSearch').value = '';
}

// ===================================
// CLASS MANAGEMENT FUNCTIONS
// ===================================

function startClass(classId) {
    if (confirm('Start this class session?')) {
        fetch(`/classes/${classId}/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Failed to start class');
            }
        })
        .catch(error => {
            showAlert('Failed to start class', 'danger');
        });
    }
}

function endClass(classId) {
    if (confirm('End this class session?')) {
        fetch(`/classes/${classId}/end`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Failed to end class');
            }
        })
        .catch(error => {
            showAlert('Failed to end class', 'danger');
        });
    }
}

// ===================================
// ATTENDANCE FUNCTIONS
// ===================================

function markAttendance(classId, studentId, status) {
    const formData = new FormData();
    formData.append('student_id', studentId);
    formData.append('status', status);
    formData.append('arrival_time', document.getElementById('arrivalTime')?.value || '');
    formData.append('late_minutes', document.getElementById('lateMinutes')?.value || '0');
    formData.append('participation_level', document.getElementById('participationLevel')?.value || '');
    formData.append('behavior_notes', document.getElementById('behaviorNotes')?.value || '');
    formData.append('homework_submitted', document.getElementById('homeworkSubmitted')?.checked || false);
    
    fetch(`/classes/${classId}/attendance`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (response.ok) {
            showAlert('Attendance marked successfully', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error('Failed to mark attendance');
        }
    })
    .catch(error => {
        showAlert('Failed to mark attendance', 'danger');
    });
}

// ===================================
// DEPARTMENT FUNCTIONS
// ===================================

function deleteDepartment(deptId, deptName) {
    if (confirm(`Delete department "${deptName}"? This action cannot be undone.`)) {
        fetch(`/departments/${deptId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => {
            showAlert('Failed to delete department', 'danger');
        });
    }
}

// ===================================
// FINANCE FUNCTIONS
// ===================================

function processPayment(feeId) {
    const amount = document.getElementById(`amount_${feeId}`).value;
    const paymentMethod = document.getElementById(`payment_method_${feeId}`).value;
    const transactionId = document.getElementById(`transaction_id_${feeId}`).value;
    
    if (!amount || !paymentMethod) {
        showAlert('Please fill in all required fields', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('amount', amount);
    formData.append('payment_method', paymentMethod);
    formData.append('transaction_id', transactionId);
    formData.append('payment_date', new Date().toISOString().split('T')[0]);
    
    fetch(`/finance/fees/${feeId}/pay`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (response.ok) {
            showAlert('Payment processed successfully', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error('Payment processing failed');
        }
    })
    .catch(error => {
        showAlert('Payment processing failed', 'danger');
    });
}

// ===================================
// UTILITY FUNCTIONS
// ===================================

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

function confirmDelete(itemName, deleteUrl) {
    if (confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = deleteUrl;
        
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrf_token';
            tokenInput.value = csrfToken;
            form.appendChild(tokenInput);
        }
        
        document.body.appendChild(form);
        form.submit();
    }
}

// ===================================
// FORM VALIDATION
// ===================================

function validateForm(formId) {
    const form = document.getElementById(formId);
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    if (!isValid) {
        showAlert('Please fill in all required fields', 'warning');
    }
    
    return isValid;
}

// ===================================
// DYNAMIC FORM FIELDS
// ===================================

function addSubject() {
    const container = document.getElementById('subjectsContainer');
    const index = container.children.length;
    
    const subjectDiv = document.createElement('div');
    subjectDiv.className = 'subject-entry mb-3';
    subjectDiv.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <input type="text" name="subjects[${index}][name]" class="form-control" placeholder="Subject name" required>
            </div>
            <div class="col-md-3">
                <select name="subjects[${index}][tutor_id]" class="form-control" required>
                    <option value="">Select Tutor</option>
                    ${getTutorOptions()}
                </select>
            </div>
            <div class="col-md-2">
                <input type="number" name="subjects[${index}][sessions_per_week]" class="form-control" placeholder="Sessions/week" value="1" min="1">
            </div>
            <div class="col-md-2">
                <input type="number" name="subjects[${index}][duration]" class="form-control" placeholder="Duration (min)" value="60" min="30">
            </div>
            <div class="col-md-1">
                <button type="button" class="btn btn-danger btn-sm" onclick="removeSubject(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    container.appendChild(subjectDiv);
}

function removeSubject(button) {
    button.closest('.subject-entry').remove();
}

function getTutorOptions() {
    // This would be populated from your backend data
    // For now, returning empty string - should be populated by your template
    return '';
}

// ===================================
// CALENDAR FUNCTIONS
// ===================================

function initializeCalendar() {
    // Calendar initialization for schedule view
    // This would integrate with a calendar library like FullCalendar
    console.log('Initializing calendar...');
}

// ===================================
// EXPORT FUNCTIONS
// ===================================

function exportData(type, format = 'csv') {
    const params = new URLSearchParams(window.location.search);
    params.append('export', format);
    
    window.location.href = `/reports/${type}?${params.toString()}`;
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
    
    // Initialize form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                showAlert('Please fill in all required fields correctly', 'warning');
            }
            form.classList.add('was-validated');
        });
    });
    
    // Initialize search functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if (this.dataset.searchType === 'students') {
                    searchStudents(this.value);
                }
            }, 300);
        });
    });
    
    // Initialize calendar if element exists
    if (document.getElementById('calendar')) {
        initializeCalendar();
    }
    
    // Auto-save drafts for forms
    const draftForms = document.querySelectorAll('.auto-save-form');
    draftForms.forEach(form => {
        const formId = form.id;
        
        // Load saved draft
        const savedData = localStorage.getItem(`draft_${formId}`);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = form.querySelector(`[name="${key}"]`);
                    if (field) {
                        field.value = data[key];
                    }
                });
            } catch (e) {
                console.warn('Failed to load form draft');
            }
        }
        
        // Save draft on input
        form.addEventListener('input', debounce(() => {
            const formData = new FormData(form);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            localStorage.setItem(`draft_${formId}`, JSON.stringify(data));
        }, 1000));
        
        // Clear draft on successful submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(`draft_${formId}`);
        });
    });
});

// ===================================
// ADVANCED FEATURES
// ===================================

// Debounce function for auto-save
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// File upload with progress
function uploadFile(inputElement, uploadUrl) {
    const file = inputElement.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    const progressBar = document.createElement('div');
    progressBar.className = 'progress mt-2';
    progressBar.innerHTML = '<div class="progress-bar" role="progressbar"></div>';
    inputElement.parentNode.appendChild(progressBar);
    
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            progressBar.querySelector('.progress-bar').style.width = percentComplete + '%';
        }
    });
    
    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            showAlert('File uploaded successfully', 'success');
            progressBar.remove();
        } else {
            showAlert('Upload failed', 'danger');
            progressBar.remove();
        }
    });
    
    xhr.addEventListener('error', () => {
        showAlert('Upload failed', 'danger');
        progressBar.remove();
    });
    
    xhr.open('POST', uploadUrl);
    xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
    xhr.send(formData);
}

// Real-time notifications
function initializeNotifications() {
    // Check for new notifications every 30 seconds
    setInterval(() => {
        fetch('/api/notifications/check')
            .then(response => response.json())
            .then(data => {
                if (data.count > 0) {
                    updateNotificationBadge(data.count);
                    if (data.urgent) {
                        showUrgentNotification(data.urgent);
                    }
                }
            })
            .catch(error => {
                console.error('Notification check failed:', error);
            });
    }, 30000);
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    }
}

function showUrgentNotification(notification) {
    const toast = document.createElement('div');
    toast.className = 'toast position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast-header bg-danger text-white">
            <strong class="me-auto">Urgent Notification</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${notification.message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

// Data table enhancements
function initializeDataTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Add sorting functionality
    const headers = table.querySelectorAll('th[data-sortable]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            sortTable(table, header.cellIndex, header.dataset.sortType);
        });
    });
    
    // Add filtering
    const filterInput = document.querySelector(`#${tableId}_filter`);
    if (filterInput) {
        filterInput.addEventListener('input', () => {
            filterTable(table, filterInput.value);
        });
    }
}

function sortTable(table, columnIndex, sortType = 'text') {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (sortType === 'number') {
            return parseFloat(aValue) - parseFloat(bValue);
        } else if (sortType === 'date') {
            return new Date(aValue) - new Date(bValue);
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

function filterTable(table, filterValue) {
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const matches = text.includes(filterValue.toLowerCase());
        row.style.display = matches ? '' : 'none';
    });
}

// Form field dependencies
function setupFieldDependencies() {
    document.querySelectorAll('[data-depends-on]').forEach(field => {
        const dependsOn = field.dataset.dependsOn;
        const dependsValue = field.dataset.dependsValue;
        const parentField = document.querySelector(`[name="${dependsOn}"]`);
        
        if (parentField) {
            function toggleField() {
                const shouldShow = parentField.value === dependsValue;
                field.closest('.form-group').style.display = shouldShow ? 'block' : 'none';
                if (!shouldShow) {
                    field.value = '';
                }
            }
            
            parentField.addEventListener('change', toggleField);
            toggleField(); // Initial state
        }
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+S to save forms
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            const activeForm = document.activeElement.closest('form');
            if (activeForm) {
                activeForm.requestSubmit();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) modal.hide();
            }
        }
        
        // Ctrl+F to focus search
        if (e.ctrlKey && e.key === 'f') {
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }
    });
}

// Print functionality
function printReport(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .no-print { display: none; }
                @media print {
                    body { margin: 0; }
                    .page-break { page-break-after: always; }
                }
            </style>
        </head>
        <body>
            ${container.innerHTML}
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
}

// Initialize all functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setupFieldDependencies();
    initializeKeyboardShortcuts();
    initializeNotifications();
    
    // Initialize data tables
    document.querySelectorAll('table[data-table]').forEach(table => {
        initializeDataTable(table.id);
    });
});

// Export functions for global access
window.LMS = {
    previewForm,
    bulkUserAction,
    resetUserPassword,
    searchStudents,
    startClass,
    endClass,
    markAttendance,
    deleteDepartment,
    processPayment,
    showAlert,
    confirmDelete,
    validateForm,
    addSubject,
    removeSubject,
    exportData,
    printReport,
    uploadFile
};