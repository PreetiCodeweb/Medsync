// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentUser = null;
let authToken = null;
let currentLocation = null;

// DOM Elements
const loginForm = document.getElementById('loginForm');
const errorMessage = document.getElementById('errorMessage');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    console.log('MedSync frontend loaded');
    checkAuth();
    setupEventListeners();
});

function checkAuth() {
    const storedToken = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('currentUser');
    
    if (storedToken && storedUser) {
        authToken = storedToken;
        currentUser = JSON.parse(storedUser);
        
        // Redirect to appropriate portal
        if (currentUser.role === 'user') {
            window.location.href = 'user_portal.html';
        } else if (currentUser.role === 'hospital') {
            window.location.href = 'hospital_portal.html';
        }
    }
}

function setupEventListeners() {
    // Login form
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // User portal listeners
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    const ambulanceBtn = document.getElementById('ambulanceBtn');
    if (ambulanceBtn) {
        ambulanceBtn.addEventListener('click', handleAmbulance);
    }
    
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }
    
    const gpsBtn = document.getElementById('gpsBtn');
    if (gpsBtn) {
        gpsBtn.addEventListener('click', handleGPS);
    }
    
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', handleVoiceInput);
    }
    
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleSymptomAnalysis);
    }
    
    // Hospital portal listeners
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', handleTabSwitch);
    });
    
    const addHospitalBtn = document.getElementById('addHospitalBtn');
    if (addHospitalBtn) {
        addHospitalBtn.addEventListener('click', () => openModal('hospitalModal'));
    }
    
    const addDoctorBtn = document.getElementById('addDoctorBtn');
    if (addDoctorBtn) {
        addDoctorBtn.addEventListener('click', () => {
            loadHospitalsForSelect('doctorHospital');
            openModal('doctorModal');
        });
    }
    
    const addDepartmentBtn = document.getElementById('addDepartmentBtn');
    if (addDepartmentBtn) {
        addDepartmentBtn.addEventListener('click', () => {
            loadHospitalsForSelect('departmentHospital');
            openModal('departmentModal');
        });
    }
    
    // Form submissions
    const hospitalForm = document.getElementById('hospitalForm');
    if (hospitalForm) {
        hospitalForm.addEventListener('submit', handleHospitalSubmit);
    }
    
    const doctorForm = document.getElementById('doctorForm');
    if (doctorForm) {
        doctorForm.addEventListener('submit', handleDoctorSubmit);
    }
    
    const departmentForm = document.getElementById('departmentForm');
    if (departmentForm) {
        departmentForm.addEventListener('submit', handleDepartmentSubmit);
    }
    
    // Modal close buttons
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    // Load management data if on hospital portal
    if (window.location.pathname.includes('hospital_portal.html')) {
        loadManagementData();
    }
    
    // Load hospitals if on user portal
    if (window.location.pathname.includes('user_portal.html')) {
        loadHospitals();
    }
}

// Authentication functions
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            currentUser = { email, role: data.role };
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            // Redirect to appropriate portal
            if (data.role === 'user') {
                window.location.href = 'user_portal.html';
            } else if (data.role === 'hospital') {
                window.location.href = 'hospital_portal.html';
            }
        } else {
            showError(data.detail || 'Login failed');
        }
    } catch (error) {
        showError('Network error. Please try again.');
    }
}

function handleLogout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    authToken = null;
    currentUser = null;
    window.location.href = 'index.html';
}

function showError(message) {
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
}

// User portal functions
async function loadHospitals() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/hospitals`);
        const hospitals = await response.json();
        
        const hospitalsList = document.getElementById('hospitalsList');
        if (hospitalsList) {
            hospitalsList.innerHTML = hospitals.map(hospital => `
                <div class="hospital-card" onclick="showHospitalDetails(${hospital.id})">
                    <h3>${hospital.name}</h3>
                    <p>📍 ${hospital.address}</p>
                    <p>📞 ${hospital.phone}</p>
                    <div class="bed-info">
                        <span class="bed-count">🛏️ Emergency: ${hospital.emergency_beds}</span>
                        <span class="bed-count icu">🏥 ICU: ${hospital.icu_beds}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading hospitals:', error);
    }
}

async function showHospitalDetails(hospitalId) {
    try {
        // Get hospital details
        const hospitalsResponse = await fetch(`${API_BASE_URL}/api/hospitals`);
        const hospitals = await hospitalsResponse.json();
        const hospital = hospitals.find(h => h.id === hospitalId);
        
        // Get doctors for this hospital
        const doctorsResponse = await fetch(`${API_BASE_URL}/api/hospitals/${hospitalId}/doctors`);
        const doctors = await doctorsResponse.json();
        
        // Get departments for this hospital
        const departmentsResponse = await fetch(`${API_BASE_URL}/api/hospitals/${hospitalId}/departments`);
        const departments = await departmentsResponse.json();
        
        const modal = document.getElementById('hospitalModal');
        const detailsContainer = document.getElementById('hospitalDetails');
        
        detailsContainer.innerHTML = `
            <div class="hospital-detail-info">
                <h3>${hospital.name}</h3>
                <p>📍 ${hospital.address}</p>
                <p>📞 ${hospital.phone}</p>
                <div class="bed-info">
                    <span class="bed-count">🛏️ Emergency Beds: ${hospital.emergency_beds}</span>
                    <span class="bed-count icu">🏥 ICU Beds: ${hospital.icu_beds}</span>
                </div>
            </div>
            
            <h4>Available Doctors</h4>
            <div class="doctor-list">
                ${doctors.length > 0 ? doctors.map(doctor => `
                    <div class="doctor-item">
                        <h4>${doctor.name} ${doctor.available ? '✅' : '❌'}</h4>
                        <p>🏥 Department: ${doctor.department}</p>
                        <p>🎯 Specialization: ${doctor.specialization}</p>
                        <p>📞 Phone: ${doctor.phone}</p>
                    </div>
                `).join('') : '<p>No doctors available</p>'}
            </div>
            
            <h4>Departments</h4>
            <div class="department-list">
                ${departments.length > 0 ? departments.map(dept => `
                    <div class="department-item">
                        <h4>${dept.name}</h4>
                        <p>${dept.description}</p>
                    </div>
                `).join('') : '<p>No departments available</p>'}
            </div>
        `;
        
        modal.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading hospital details:', error);
    }
}

function handleAmbulance() {
    const confirmed = confirm('🚨 EMERGENCY AMBULANCE\n\nAn ambulance will be dispatched to your current location.\n\nContinue?');
    if (confirmed) {
        alert('🚨 Ambulance dispatched! Help is on the way.\n\nLocation: ' + (currentLocation || 'Your current location'));
        // In a real app, this would call emergency services
    }
}

function handleSearch() {
    const location = document.getElementById('locationInput').value;
    if (location) {
        currentLocation = location;
        loadHospitals();
    } else {
        alert('Please enter a location');
    }
}

function handleGPS() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                currentLocation = `${position.coords.latitude}, ${position.coords.longitude}`;
                document.getElementById('locationInput').value = currentLocation;
                loadHospitals();
            },
            (error) => {
                alert('Unable to get your location. Please enter it manually.');
            }
        );
    } else {
        alert('Geolocation is not supported by your browser.');
    }
}

// Voice input and AI analysis
let recognition = null;

function handleVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Voice recognition is not supported in your browser. Please use Chrome or type your symptoms.');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (recognition && recognition.state === 'listening') {
        recognition.stop();
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = function() {
        document.getElementById('voiceStatus').textContent = 'Listening... Speak now';
        document.getElementById('voiceBtn').textContent = '⏹️ Stop Recording';
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('symptomText').value = transcript;
        document.getElementById('voiceStatus').textContent = 'Recorded: ' + transcript;
        document.getElementById('voiceBtn').textContent = '🎤 Record Again';
    };
    
    recognition.onerror = function(event) {
        document.getElementById('voiceStatus').textContent = 'Error: ' + event.error;
        document.getElementById('voiceBtn').textContent = '🎤 Try Again';
    };
    
    recognition.onend = function() {
        document.getElementById('voiceBtn').textContent = '🎤 Record Again';
    };
    
    recognition.start();
}

async function handleSymptomAnalysis() {
    const symptoms = document.getElementById('symptomText').value;
    const useRag = document.getElementById('useRag').checked;
    
    if (!symptoms.trim()) {
        alert('Please describe your symptoms first');
        return;
    }
    
    // Show loading state
    const analyzeBtn = document.getElementById('analyzeBtn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.textContent = 'Analyzing...';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/ai/symptom-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                symptoms: symptoms,
                user_location: currentLocation,
                include_rag: useRag
            })
        });
        
        const result = await response.json();
        
        const aiResultDiv = document.getElementById('aiResult');
        aiResultDiv.classList.remove('hidden');
        
        // Build enhanced results display
        let resultsHTML = `
            <h3>🤖 AI Analysis Results</h3>
            <div class="analysis-meta">
                <span class="rag-badge ${result.rag_enabled ? 'rag-enabled' : 'rag-disabled'}">
                    ${result.rag_enabled ? '🧠 RAG-Powered' : '⚠️ Fallback Analysis'}
                </span>
                ${result.confidence ? `<span class="confidence-score">Confidence: ${(result.confidence * 100).toFixed(1)}%</span>` : ''}
            </div>
            <div class="analysis-section">
                <h4>Possible Conditions</h4>
                <p>${result.possible_conditions.join(', ')}</p>
            </div>
            <div class="analysis-section">
                <h4>Recommended Department</h4>
                <p><strong>${result.recommended_department}</strong></p>
                ${result.category ? `<p class="category-tag">Category: ${result.category}</p>` : ''}
            </div>
            <div class="analysis-section">
                <h4>Severity Assessment</h4>
                <p class="severity-${result.severity}">${result.severity.toUpperCase()}</p>
            </div>
            <div class="analysis-section">
                <h4>Recommendation</h4>
                <p>${result.recommendation}</p>
            </div>
        `;
        
        // Add RAG-specific information if available
        if (result.rag_enabled && result.sources) {
            resultsHTML += `
                <div class="analysis-section rag-sources">
                    <h4>📚 Knowledge Base Sources</h4>
                    <p>This analysis is based on ${result.sources.length} medical documents from our knowledge base.</p>
                </div>
            `;
        }
        
        aiResultDiv.innerHTML = resultsHTML;
        
    } catch (error) {
        console.error('Error analyzing symptoms:', error);
        alert('Error analyzing symptoms. Please try again.');
    } finally {
        // Reset button state
        analyzeBtn.textContent = originalText;
        analyzeBtn.disabled = false;
    }
}

// Hospital management functions
function handleTabSwitch(e) {
    const tabId = e.target.dataset.tab;
    
    // Remove active class from all tabs and contents
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding content
    e.target.classList.add('active');
    document.getElementById(`${tabId}-tab`).classList.add('active');
}

async function loadManagementData() {
    await Promise.all([
        loadManagementHospitals(),
        loadManagementDoctors(),
        loadManagementDepartments()
    ]);
}

async function loadManagementHospitals() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/management/hospitals`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const hospitals = await response.json();
            const container = document.getElementById('hospitalsManagementList');
            
            container.innerHTML = hospitals.map(hospital => `
                <div class="management-item">
                    <div class="management-item-info">
                        <h3>${hospital.name}</h3>
                        <p>📍 ${hospital.address}</p>
                        <p>📞 ${hospital.phone}</p>
                        <p>🛏️ Emergency: ${hospital.emergency_beds} | ICU: ${hospital.icu_beds}</p>
                    </div>
                    <div class="management-item-actions">
                        <button class="btn btn-edit" onclick="editHospital(${hospital.id})">Edit</button>
                        <button class="btn btn-delete" onclick="deleteHospital(${hospital.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading hospitals:', error);
    }
}

async function loadManagementDoctors() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/management/doctors`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const doctors = await response.json();
            const container = document.getElementById('doctorsManagementList');
            
            container.innerHTML = doctors.map(doctor => `
                <div class="management-item">
                    <div class="management-item-info">
                        <h3>${doctor.name} ${doctor.available ? '✅' : '❌'}</h3>
                        <p>🏥 Hospital: ${doctor.hospital_name}</p>
                        <p>🏥 Department: ${doctor.department}</p>
                        <p>🎯 Specialization: ${doctor.specialization}</p>
                        <p>📞 ${doctor.phone}</p>
                    </div>
                    <div class="management-item-actions">
                        <button class="btn btn-edit" onclick="editDoctor(${doctor.id})">Edit</button>
                        <button class="btn btn-delete" onclick="deleteDoctor(${doctor.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading doctors:', error);
    }
}

async function loadManagementDepartments() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/management/departments`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const departments = await response.json();
            const container = document.getElementById('departmentsManagementList');
            
            container.innerHTML = departments.map(dept => `
                <div class="management-item">
                    <div class="management-item-info">
                        <h3>${dept.name}</h3>
                        <p>🏥 Hospital: ${dept.hospital_name}</p>
                        <p>📝 ${dept.description}</p>
                    </div>
                    <div class="management-item-actions">
                        <button class="btn btn-delete" onclick="deleteDepartment(${dept.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

async function loadHospitalsForSelect(selectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/hospitals`);
        const hospitals = await response.json();
        
        const select = document.getElementById(selectId);
        select.innerHTML = hospitals.map(h => `<option value="${h.id}">${h.name}</option>`).join('');
    } catch (error) {
        console.error('Error loading hospitals for select:', error);
    }
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => modal.classList.add('hidden'));
}

// Form handlers
async function handleHospitalSubmit(e) {
    e.preventDefault();
    
    const hospitalData = {
        name: document.getElementById('hospitalName').value,
        address: document.getElementById('hospitalAddress').value,
        phone: document.getElementById('hospitalPhone').value,
        latitude: parseFloat(document.getElementById('hospitalLat').value),
        longitude: parseFloat(document.getElementById('hospitalLng').value),
        emergency_beds: parseInt(document.getElementById('emergencyBeds').value),
        icu_beds: parseInt(document.getElementById('icuBeds').value)
    };
    
    const hospitalId = document.getElementById('hospitalId').value;
    
    try {
        const url = hospitalId ? 
            `${API_BASE_URL}/api/hospitals/${hospitalId}` : 
            `${API_BASE_URL}/api/hospitals`;
        
        const method = hospitalId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(hospitalData)
        });
        
        if (response.ok) {
            closeModal();
            loadManagementHospitals();
            document.getElementById('hospitalForm').reset();
            document.getElementById('hospitalId').value = '';
            document.getElementById('hospitalModalTitle').textContent = 'Add Hospital';
        } else {
            alert('Error saving hospital');
        }
    } catch (error) {
        console.error('Error saving hospital:', error);
        alert('Error saving hospital');
    }
}

async function handleDoctorSubmit(e) {
    e.preventDefault();
    
    const doctorData = {
        hospital_id: parseInt(document.getElementById('doctorHospital').value),
        name: document.getElementById('doctorName').value,
        department: document.getElementById('doctorDepartment').value,
        specialization: document.getElementById('doctorSpecialization').value,
        phone: document.getElementById('doctorPhone').value,
        available: document.getElementById('doctorAvailable').checked
    };
    
    const doctorId = document.getElementById('doctorId').value;
    
    try {
        const url = doctorId ? 
            `${API_BASE_URL}/api/doctors/${doctorId}` : 
            `${API_BASE_URL}/api/doctors`;
        
        const method = doctorId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(doctorData)
        });
        
        if (response.ok) {
            closeModal();
            loadManagementDoctors();
            document.getElementById('doctorForm').reset();
            document.getElementById('doctorId').value = '';
            document.getElementById('doctorModalTitle').textContent = 'Add Doctor';
        } else {
            alert('Error saving doctor');
        }
    } catch (error) {
        console.error('Error saving doctor:', error);
        alert('Error saving doctor');
    }
}

async function handleDepartmentSubmit(e) {
    e.preventDefault();
    
    const departmentData = {
        hospital_id: parseInt(document.getElementById('departmentHospital').value),
        name: document.getElementById('departmentName').value,
        description: document.getElementById('departmentDescription').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/departments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(departmentData)
        });
        
        if (response.ok) {
            closeModal();
            loadManagementDepartments();
            document.getElementById('departmentForm').reset();
        } else {
            alert('Error saving department');
        }
    } catch (error) {
        console.error('Error saving department:', error);
        alert('Error saving department');
    }
}

// Edit and delete functions
async function editHospital(hospitalId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/hospitals`);
        const hospitals = await response.json();
        const hospital = hospitals.find(h => h.id === hospitalId);
        
        if (hospital) {
            document.getElementById('hospitalId').value = hospital.id;
            document.getElementById('hospitalName').value = hospital.name;
            document.getElementById('hospitalAddress').value = hospital.address;
            document.getElementById('hospitalPhone').value = hospital.phone;
            document.getElementById('hospitalLat').value = hospital.latitude;
            document.getElementById('hospitalLng').value = hospital.longitude;
            document.getElementById('emergencyBeds').value = hospital.emergency_beds;
            document.getElementById('icuBeds').value = hospital.icu_beds;
            document.getElementById('hospitalModalTitle').textContent = 'Edit Hospital';
            openModal('hospitalModal');
        }
    } catch (error) {
        console.error('Error loading hospital for edit:', error);
    }
}

async function editDoctor(doctorId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/management/doctors`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const doctors = await response.json();
        const doctor = doctors.find(d => d.id === doctorId);
        
        if (doctor) {
            await loadHospitalsForSelect('doctorHospital');
            document.getElementById('doctorId').value = doctor.id;
            document.getElementById('doctorHospital').value = doctor.hospital_id;
            document.getElementById('doctorName').value = doctor.name;
            document.getElementById('doctorDepartment').value = doctor.department;
            document.getElementById('doctorSpecialization').value = doctor.specialization;
            document.getElementById('doctorPhone').value = doctor.phone;
            document.getElementById('doctorAvailable').checked = doctor.available;
            document.getElementById('doctorModalTitle').textContent = 'Edit Doctor';
            openModal('doctorModal');
        }
    } catch (error) {
        console.error('Error loading doctor for edit:', error);
    }
}

async function deleteHospital(hospitalId) {
    if (confirm('Are you sure you want to delete this hospital?')) {
        try {
            // Note: Delete endpoint not implemented in backend yet
            alert('Delete functionality needs to be implemented in backend');
        } catch (error) {
            console.error('Error deleting hospital:', error);
        }
    }
}

async function deleteDoctor(doctorId) {
    if (confirm('Are you sure you want to delete this doctor?')) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/doctors/${doctorId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (response.ok) {
                loadManagementDoctors();
            } else {
                alert('Error deleting doctor');
            }
        } catch (error) {
            console.error('Error deleting doctor:', error);
            alert('Error deleting doctor');
        }
    }
}

async function deleteDepartment(departmentId) {
    if (confirm('Are you sure you want to delete this department?')) {
        try {
            // Note: Delete endpoint not implemented in backend yet
            alert('Delete functionality needs to be implemented in backend');
        } catch (error) {
            console.error('Error deleting department:', error);
        }
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        closeModal();
    }
}