from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

app = FastAPI(title="MedSync Hospital Management")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            latitude REAL,
            longitude REAL,
            emergency_beds INTEGER DEFAULT 0,
            icu_beds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            specialization TEXT,
            phone TEXT,
            available BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    ''')
    
    # Departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    ''')
    
    # Check if we need to seed default data
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Seed default users
        hashed_password = pwd_context.hash("user123")
        cursor.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                      ('user@medsync.com', hashed_password, 'user'))
        
        hashed_password = pwd_context.hash("hospital123")
        cursor.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                      ('hospital@medsync.com', hashed_password, 'hospital'))
        
        # Seed sample hospitals
        cursor.execute('''
            INSERT INTO hospitals (name, address, phone, latitude, longitude, emergency_beds, icu_beds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('City General Hospital', '123 Main St', '555-0100', 40.7128, -74.0060, 5, 3))
        
        cursor.execute('''
            INSERT INTO hospitals (name, address, phone, latitude, longitude, emergency_beds, icu_beds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('St. Mary Medical Center', '456 Oak Ave', '555-0101', 40.7138, -74.0070, 8, 5))
        
        cursor.execute('''
            INSERT INTO hospitals (name, address, phone, latitude, longitude, emergency_beds, icu_beds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Metro Health Hospital', '789 Pine Rd', '555-0102', 40.7148, -74.0080, 3, 2))
        
        # Seed sample doctors
        cursor.execute('''
            INSERT INTO doctors (hospital_id, name, department, specialization, phone, available)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, 'Dr. John Smith', 'Emergency', 'Trauma Care', '555-0200', 1))
        
        cursor.execute('''
            INSERT INTO doctors (hospital_id, name, department, specialization, phone, available)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, 'Dr. Sarah Johnson', 'Cardiology', 'Heart Specialist', '555-0201', 1))
        
        cursor.execute('''
            INSERT INTO doctors (hospital_id, name, department, specialization, phone, available)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (2, 'Dr. Michael Brown', 'Neurology', 'Brain Specialist', '555-0202', 1))
        
        cursor.execute('''
            INSERT INTO doctors (hospital_id, name, department, specialization, phone, available)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (2, 'Dr. Emily Davis', 'Orthopedics', 'Bone Specialist', '555-0203', 0))
        
        cursor.execute('''
            INSERT INTO doctors (hospital_id, name, department, specialization, phone, available)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (3, 'Dr. Robert Wilson', 'Pediatrics', 'Child Specialist', '555-0204', 1))
        
        # Seed departments
        cursor.execute('''
            INSERT INTO departments (hospital_id, name, description)
            VALUES (?, ?, ?)
        ''', (1, 'Emergency', '24/7 emergency care'))
        
        cursor.execute('''
            INSERT INTO departments (hospital_id, name, description)
            VALUES (?, ?, ?)
        ''', (1, 'Cardiology', 'Heart care and treatment'))
        
        cursor.execute('''
            INSERT INTO departments (hospital_id, name, description)
            VALUES (?, ?, ?)
        ''', (2, 'Neurology', 'Brain and nervous system care'))
        
        cursor.execute('''
            INSERT INTO departments (hospital_id, name, description)
            VALUES (?, ?, ?)
        ''', (3, 'Pediatrics', 'Child healthcare'))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class HospitalCreate(BaseModel):
    name: str
    address: str
    phone: str
    latitude: float
    longitude: float
    emergency_beds: int
    icu_beds: int

class DoctorCreate(BaseModel):
    hospital_id: int
    name: str
    department: str
    specialization: str
    phone: str
    available: bool

class DepartmentCreate(BaseModel):
    hospital_id: int
    name: str
    description: str

class SymptomAnalysis(BaseModel):
    symptoms: str
    user_location: Optional[str] = None

# Authentication functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.post("/api/login")
def login(request: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (request.email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not pwd_context.verify(request.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user['email'], "role": user['role']})
    return {"access_token": access_token, "token_type": "bearer", "role": user['role']}

@app.get("/api/hospitals")
def get_hospitals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM hospitals')
    hospitals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return hospitals

@app.get("/api/hospitals/{hospital_id}/doctors")
def get_hospital_doctors(hospital_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM doctors WHERE hospital_id = ?', (hospital_id,))
    doctors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return doctors

@app.get("/api/hospitals/{hospital_id}/departments")
def get_hospital_departments(hospital_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments WHERE hospital_id = ?', (hospital_id,))
    departments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return departments

@app.post("/api/hospitals")
def create_hospital(hospital: HospitalCreate, current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can create hospitals")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, latitude, longitude, emergency_beds, icu_beds)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (hospital.name, hospital.address, hospital.phone, hospital.latitude, 
          hospital.longitude, hospital.emergency_beds, hospital.icu_beds))
    conn.commit()
    hospital_id = cursor.lastrowid
    conn.close()
    return {"id": hospital_id, "message": "Hospital created successfully"}

@app.put("/api/hospitals/{hospital_id}")
def update_hospital(hospital_id: int, hospital: HospitalCreate, current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can update hospitals")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE hospitals SET name=?, address=?, phone=?, latitude=?, longitude=?, 
        emergency_beds=?, icu_beds=? WHERE id=?
    ''', (hospital.name, hospital.address, hospital.phone, hospital.latitude, 
          hospital.longitude, hospital.emergency_beds, hospital.icu_beds, hospital_id))
    conn.commit()
    conn.close()
    return {"message": "Hospital updated successfully"}

@app.post("/api/doctors")
def create_doctor(doctor: DoctorCreate, current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can create doctors")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO doctors (hospital_id, name, department, specialization, phone, available)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (doctor.hospital_id, doctor.name, doctor.department, doctor.specialization, 
          doctor.phone, doctor.available))
    conn.commit()
    doctor_id = cursor.lastrowid
    conn.close()
    return {"id": doctor_id, "message": "Doctor created successfully"}

@app.put("/api/doctors/{doctor_id}")
def update_doctor(doctor_id: int, doctor: DoctorCreate, current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can update doctors")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE doctors SET hospital_id=?, name=?, department=?, specialization=?, 
        phone=?, available=? WHERE id=?
    ''', (doctor.hospital_id, doctor.name, doctor.department, doctor.specialization, 
          doctor.phone, doctor.available, doctor_id))
    conn.commit()
    conn.close()
    return {"message": "Doctor updated successfully"}

@app.delete("/api/doctors/{doctor_id}")
def delete_doctor(doctor_id: int, current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can delete doctors")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
    conn.commit()
    conn.close()
    return {"message": "Doctor deleted successfully"}

@app.post("/api/departments")
def create_department(department: DepartmentCreate, current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can create departments")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO departments (hospital_id, name, description)
        VALUES (?, ?, ?)
    ''', (department.hospital_id, department.name, department.description))
    conn.commit()
    department_id = cursor.lastrowid
    conn.close()
    return {"id": department_id, "message": "Department created successfully"}

@app.post("/api/ai/symptom-analysis")
def analyze_symptoms(analysis: SymptomAnalysis):
    # AI Symptom Analysis - RAG-based system
    # This would connect to an AI service like OpenAI or similar
    # For now, we'll provide a simulated response
    
    symptoms_lower = analysis.symptoms.lower()
    
    # Simple keyword-based analysis (would be replaced with actual AI)
    analysis_result = {
        "possible_conditions": [],
        "recommended_department": "General",
        "severity": "low",
        "recommendation": "Please consult with a healthcare professional for proper diagnosis."
    }
    
    if any(word in symptoms_lower for word in ['chest', 'heart', 'breath']):
        analysis_result["possible_conditions"] = ["Possible cardiac issue", "Respiratory problem"]
        analysis_result["recommended_department"] = "Cardiology"
        analysis_result["severity"] = "high"
        analysis_result["recommendation"] = "Immediate medical attention recommended. Please visit emergency or cardiology department."
    
    elif any(word in symptoms_lower for word in ['head', 'migraine', 'dizzy']):
        analysis_result["possible_conditions"] = ["Migraine", "Headache", "Neurological issue"]
        analysis_result["recommended_department"] = "Neurology"
        analysis_result["severity"] = "medium"
        analysis_result["recommendation"] = "Consult with neurologist for proper evaluation."
    
    elif any(word in symptoms_lower for word in ['bone', 'joint', 'muscle', 'fracture']):
        analysis_result["possible_conditions"] = ["Musculoskeletal injury", "Fracture", "Joint pain"]
        analysis_result["recommended_department"] = "Orthopedics"
        analysis_result["severity"] = "medium"
        analysis_result["recommendation"] = "Orthopedic consultation recommended for proper diagnosis and treatment."
    
    elif any(word in symptoms_lower for word in ['fever', 'cough', 'cold', 'flu']):
        analysis_result["possible_conditions"] = ["Viral infection", "Flu", "Common cold"]
        analysis_result["recommended_department"] = "General Medicine"
        analysis_result["severity"] = "low"
        analysis_result["recommendation"] = "Rest and hydration recommended. Consult if symptoms persist."
    
    elif any(word in symptoms_lower for word in ['stomach', 'digestion', 'nausea']):
        analysis_result["possible_conditions"] = ["Digestive issue", "Gastric problem"]
        analysis_result["recommended_department"] = "Gastroenterology"
        analysis_result["severity"] = "low"
        analysis_result["recommendation"] = "Consult with gastroenterologist for proper evaluation."
    
    else:
        analysis_result["possible_conditions"] = ["General condition"]
        analysis_result["recommended_department"] = "General Medicine"
        analysis_result["severity"] = "low"
        analysis_result["recommendation"] = "Please consult with a healthcare professional for proper diagnosis."
    
    return analysis_result

@app.get("/api/management/hospitals")
def get_management_hospitals(current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can access this endpoint")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM hospitals')
    hospitals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return hospitals

@app.get("/api/management/doctors")
def get_management_doctors(current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can access this endpoint")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT doctors.*, hospitals.name as hospital_name 
        FROM doctors 
        JOIN hospitals ON doctors.hospital_id = hospitals.id
    ''')
    doctors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return doctors

@app.get("/api/management/departments")
def get_management_departments(current_user: dict = Depends(verify_token)):
    if current_user['role'] != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital users can access this endpoint")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT departments.*, hospitals.name as hospital_name 
        FROM departments 
        JOIN hospitals ON departments.hospital_id = hospitals.id
    ''')
    departments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return departments

@app.get("/")
def root():
    return {"name": "MedSync", "version": "1.0.0", "status": "operational", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "medsync-hospital-management", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)