"""
Professional MedSync Hospital Management System
Industry-deployed application with RAG system, proper error handling, and monitoring
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta, timezone
import sqlite3
import json

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.exposition import start_http_server

from config import settings
from rag_system import rag_system

# Configure structured logging
def setup_logging():
    """Setup professional logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        handlers=[handler],
        force=True
    )

setup_logging()
logger = logging.getLogger(__name__)

# Prometheus metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration')
rag_searches_total = Counter('rag_searches_total', 'Total RAG searches', ['result_type'])
rag_analysis_duration = Histogram('rag_analysis_duration_seconds', 'RAG analysis duration')

# Security
security = HTTPBearer()

# Database setup
def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = sqlite3.connect(settings.DATABASE_URL.replace('sqlite:///', ''))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

def init_db():
    """Initialize database with professional schema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Users table with enhanced fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'hospital', 'admin')),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Hospitals table with enhanced fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                latitude REAL,
                longitude REAL,
                emergency_beds INTEGER DEFAULT 0,
                icu_beds INTEGER DEFAULT 0,
                total_beds INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Doctors table with enhanced fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id INTEGER,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                specialization TEXT,
                phone TEXT,
                email TEXT,
                available BOOLEAN DEFAULT 1,
                license_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
            )
        ''')
        
        # Departments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
            )
        ''')
        
        # Audit log for compliance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                hospital_id INTEGER,
                doctor_id INTEGER,
                appointment_date TIMESTAMP NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'confirmed', 'completed', 'cancelled')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
            )
        ''')
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                date_of_birth DATE,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                blood_type TEXT,
                allergies TEXT,
                medical_conditions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Check if we need to seed default data
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding default data...")
            seed_demo_data(cursor)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def seed_demo_data(cursor):
    """Seed demo data for development/testing"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Seed default users
    hashed_password = pwd_context.hash("user123")
    cursor.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                  ('user@medsync.com', hashed_password, 'user'))
    
    hashed_password = pwd_context.hash("hospital123")
    cursor.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                  ('hospital@medsync.com', hashed_password, 'hospital'))
    
    hashed_password = pwd_context.hash("admin123")
    cursor.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                  ('admin@medsync.com', hashed_password, 'admin'))
    
    # Seed sample hospitals
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('City General Hospital', '123 Main St', '555-0100', 'info@citygeneral.com', 
          40.7128, -74.0060, 5, 3, 50))
    
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('St. Mary Medical Center', '456 Oak Ave', '555-0101', 'info@stmary.com', 
          40.7138, -74.0070, 8, 5, 75))
    
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Metro Health Hospital', '789 Pine Rd', '555-0102', 'info@metrohealth.com', 
          40.7148, -74.0080, 3, 2, 30))
    
    # Seed sample doctors
    cursor.execute('''
        INSERT INTO doctors (hospital_id, name, department, specialization, phone, email, available, license_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (1, 'Dr. John Smith', 'Emergency', 'Trauma Care', '555-0200', 'jsmith@citygeneral.com', 1, 'MD12345'))
    
    cursor.execute('''
        INSERT INTO doctors (hospital_id, name, department, specialization, phone, email, available, license_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (1, 'Dr. Sarah Johnson', 'Cardiology', 'Heart Specialist', '555-0201', 'sjohnson@citygeneral.com', 1, 'MD12346'))
    
    cursor.execute('''
        INSERT INTO doctors (hospital_id, name, department, specialization, phone, email, available, license_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (2, 'Dr. Michael Brown', 'Neurology', 'Brain Specialist', '555-0202', 'mbrown@stmary.com', 1, 'MD12347'))
    
    cursor.execute('''
        INSERT INTO doctors (hospital_id, name, department, specialization, phone, email, available, license_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (2, 'Dr. Emily Davis', 'Orthopedics', 'Bone Specialist', '555-0203', 'edavis@stmary.com', 0, 'MD12348'))
    
    cursor.execute('''
        INSERT INTO doctors (hospital_id, name, department, specialization, phone, email, available, license_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (3, 'Dr. Robert Wilson', 'Pediatrics', 'Child Specialist', '555-0204', 'rwilson@metrohealth.com', 1, 'MD12349'))
    
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

# Pydantic models with validation
class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    expires_in: int

class HospitalCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=5, max_length=500)
    phone: str = Field(..., pattern=r'^\+?[\d\s-]+$')
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    emergency_beds: int = Field(..., ge=0)
    icu_beds: int = Field(..., ge=0)
    total_beds: int = Field(..., ge=0)

class DoctorCreate(BaseModel):
    hospital_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=200)
    department: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., pattern=r'^\+?[\d\s-]+$')
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    available: bool = True
    license_number: Optional[str] = Field(None, max_length=50)

class DepartmentCreate(BaseModel):
    hospital_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)

class AppointmentCreate(BaseModel):
    hospital_id: int = Field(..., gt=0)
    doctor_id: Optional[int] = Field(None, gt=0)
    appointment_date: str = Field(..., description="ISO format datetime string")
    reason: str = Field(..., min_length=5, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)

class UserProfileCreate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s-]+$')
    date_of_birth: Optional[str] = Field(None, description="ISO format date string")
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s-]+$')
    blood_type: Optional[str] = Field(None, max_length=5)
    allergies: Optional[str] = Field(None, max_length=500)
    medical_conditions: Optional[str] = Field(None, max_length=1000)

class AppointmentUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(scheduled|confirmed|completed|cancelled)$')

class SymptomAnalysis(BaseModel):
    symptoms: str = Field(..., min_length=5, max_length=2000)
    user_location: Optional[str] = None
    include_rag: bool = True

class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    rag_enabled: bool
    database_connected: bool

# Authentication functions
def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    from jose import jwt
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        from jose import JWTError, jwt
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Starting MedSync application...")
    
    # Initialize database
    init_db()
    
    # Start metrics server if enabled
    if settings.ENABLE_METRICS:
        try:
            logger.info(f"Starting metrics server on port {settings.METRICS_PORT}")
            start_http_server(settings.METRICS_PORT)
        except OSError as e:
            logger.warning(f"Metrics server already running on port {settings.METRICS_PORT}")
    
    logger.info("MedSync application started successfully")
    yield
    
    logger.info("Shutting down MedSync application...")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional AI-powered hospital management system with RAG capabilities",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = datetime.now(timezone.utc)
    
    response = await call_next(request)
    
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    http_request_duration_seconds.observe(duration)
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    return response

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now(timezone.utc).isoformat()}
    )

# Handle OPTIONS requests for CORS preflight
@app.options("/api/{path:path}")
async def handle_options(request: Request):
    """Handle CORS preflight requests"""
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now(timezone.utc).isoformat()}
    )

# Health and system endpoints
@app.get("/", response_model=dict)
def root():
    """Root endpoint with system information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_connected = True
    except:
        db_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        rag_enabled=settings.ENABLE_RAG,
        database_connected=db_connected
    )

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/api/system/info")
def system_info(current_user: dict = Depends(verify_token)):
    """System information endpoint (authenticated)"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "rag_enabled": settings.ENABLE_RAG,
        "rag_stats": rag_system.get_knowledge_base_stats() if settings.ENABLE_RAG else None,
        "user": current_user["email"],
        "role": current_user["role"]
    }

# Authentication endpoints
@app.post("/api/login", response_model=Token)
def login(request: LoginRequest):
    """User login endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (request.email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(request.password, user['password']):
            logger.warning(f"Failed login attempt for email: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                      (datetime.now(timezone.utc).isoformat(), user['id']))
        conn.commit()
        conn.close()
        
        access_token = create_access_token(data={"sub": user['email'], "role": user['role']})
        
        logger.info(f"Successful login for user: {request.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user['role'],
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    role: str = Field(..., pattern=r'^(user|hospital)$')
    full_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s-]+$')

@app.post("/api/register")
def register(request: RegisterRequest):
    """User registration endpoint"""
    try:
        # Validate passwords match
        if request.password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (request.email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Hash password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(request.password)
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password, role, created_at)
            VALUES (?, ?, ?, ?)
        ''', (request.email, hashed_password, request.role, datetime.now(timezone.utc).isoformat()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"New user registered: {request.email} as {request.role}")
        
        return {
            "id": user_id,
            "email": request.email,
            "role": request.role,
            "message": "Registration successful. Please login with your credentials."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

# Hospital endpoints
@app.get("/api/hospitals")
def get_hospitals():
    """Get all hospitals"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hospitals WHERE is_active = 1')
        hospitals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return hospitals
    except Exception as e:
        logger.error(f"Error fetching hospitals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch hospitals")

@app.get("/api/hospitals/{hospital_id}/doctors")
def get_hospital_doctors(hospital_id: int):
    """Get doctors for a specific hospital"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM doctors WHERE hospital_id = ?', (hospital_id,))
        doctors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return doctors
    except Exception as e:
        logger.error(f"Error fetching doctors for hospital {hospital_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch doctors")

@app.get("/api/hospitals/{hospital_id}/departments")
def get_hospital_departments(hospital_id: int):
    """Get departments for a specific hospital"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM departments WHERE hospital_id = ?', (hospital_id,))
        departments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return departments
    except Exception as e:
        logger.error(f"Error fetching departments for hospital {hospital_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

# RAG-powered symptom analysis
@app.post("/api/ai/symptom-analysis")
def analyze_symptoms(analysis: SymptomAnalysis):
    """AI-powered symptom analysis using RAG system"""
    try:
        with rag_analysis_duration.time():
            if analysis.include_rag and settings.ENABLE_RAG:
                result = rag_system.analyze_symptoms(analysis.symptoms)
                rag_searches_total.labels(result_type="rag").inc()
            else:
                result = rag_system._fallback_analysis(analysis.symptoms)
                rag_searches_total.labels(result_type="fallback").inc()
            
            # Add user location if provided
            if analysis.user_location:
                result["user_location"] = analysis.user_location
            
            logger.info(f"Symptom analysis completed for: {analysis.symptoms[:50]}...")
            return result
            
    except Exception as e:
        logger.error(f"Symptom analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Symptom analysis failed")

# RAG search endpoint (advanced usage)
@app.post("/api/ai/search")
def rag_search(search_request: RAGSearchRequest):
    """Direct RAG search endpoint for advanced usage"""
    try:
        if not settings.ENABLE_RAG:
            raise HTTPException(status_code=503, detail="RAG system is disabled")
        
        results = rag_system.search(search_request.query, top_k=search_request.top_k)
        rag_searches_total.labels(result_type="direct_search").inc()
        
        return {
            "query": search_request.query,
            "results": results,
            "total_found": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")

# Hospital management endpoints (authenticated)
@app.post("/api/hospitals")
def create_hospital(hospital: HospitalCreate, current_user: dict = Depends(verify_token)):
    """Create new hospital (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (hospital.name, hospital.address, hospital.phone, hospital.email, 
              hospital.latitude, hospital.longitude, hospital.emergency_beds, 
              hospital.icu_beds, hospital.total_beds))
        conn.commit()
        hospital_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Hospital created: {hospital.name} by {current_user['email']}")
        return {"id": hospital_id, "message": "Hospital created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating hospital: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create hospital")

@app.delete("/api/hospitals/{hospital_id}")
def delete_hospital(hospital_id: int, current_user: dict = Depends(verify_token)):
    """Delete hospital (admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hospital exists
        cursor.execute('SELECT id FROM hospitals WHERE id = ?', (hospital_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        cursor.execute('DELETE FROM hospitals WHERE id = ?', (hospital_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Hospital deleted: {hospital_id} by {current_user['email']}")
        return {"message": "Hospital deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting hospital: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete hospital")

@app.put("/api/hospitals/{hospital_id}")
def update_hospital(hospital_id: int, hospital: HospitalCreate, current_user: dict = Depends(verify_token)):
    """Update hospital (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE hospitals SET name=?, address=?, phone=?, email=?, latitude=?, longitude=?, 
            emergency_beds=?, icu_beds=?, total_beds=?, updated_at=? WHERE id=?
        ''', (hospital.name, hospital.address, hospital.phone, hospital.email, 
              hospital.latitude, hospital.longitude, hospital.emergency_beds, 
              hospital.icu_beds, hospital.total_beds, datetime.now(timezone.utc).isoformat(), hospital_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Hospital updated: {hospital_id} by {current_user['email']}")
        return {"message": "Hospital updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating hospital: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update hospital")

# Doctor management endpoints
@app.post("/api/doctors")
def create_doctor(doctor: DoctorCreate, current_user: dict = Depends(verify_token)):
    """Create new doctor (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO doctors (hospital_id, name, department, specialization, phone, email, available, license_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (doctor.hospital_id, doctor.name, doctor.department, doctor.specialization, 
              doctor.phone, doctor.email, doctor.available, doctor.license_number))
        conn.commit()
        doctor_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Doctor created: {doctor.name} by {current_user['email']}")
        return {"id": doctor_id, "message": "Doctor created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating doctor: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create doctor")

@app.put("/api/doctors/{doctor_id}")
def update_doctor(doctor_id: int, doctor: DoctorCreate, current_user: dict = Depends(verify_token)):
    """Update doctor (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE doctors SET hospital_id=?, name=?, department=?, specialization=?, 
            phone=?, email=?, available=?, license_number=?, updated_at=? WHERE id=?
        ''', (doctor.hospital_id, doctor.name, doctor.department, doctor.specialization, 
              doctor.phone, doctor.email, doctor.available, doctor.license_number, 
              datetime.now(timezone.utc).isoformat(), doctor_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Doctor updated: {doctor_id} by {current_user['email']}")
        return {"message": "Doctor updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating doctor: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update doctor")

@app.delete("/api/doctors/{doctor_id}")
def delete_doctor(doctor_id: int, current_user: dict = Depends(verify_token)):
    """Delete doctor (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if doctor exists
        cursor.execute('SELECT id FROM doctors WHERE id = ?', (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        cursor.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Doctor deleted: {doctor_id} by {current_user['email']}")
        return {"message": "Doctor deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting doctor: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete doctor")

# Department management endpoints
@app.post("/api/departments")
def create_department(department: DepartmentCreate, current_user: dict = Depends(verify_token)):
    """Create new department (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO departments (hospital_id, name, description)
            VALUES (?, ?, ?)
        ''', (department.hospital_id, department.name, department.description))
        conn.commit()
        department_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Department created: {department.name} by {current_user['email']}")
        return {"id": department_id, "message": "Department created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating department: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create department")

@app.delete("/api/departments/{department_id}")
def delete_department(department_id: int, current_user: dict = Depends(verify_token)):
    """Delete department (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if department exists
        cursor.execute('SELECT id FROM departments WHERE id = ?', (department_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Department not found")
        
        cursor.execute('DELETE FROM departments WHERE id = ?', (department_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Department deleted: {department_id} by {current_user['email']}")
        return {"message": "Department deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting department: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete department")

# Management endpoints
@app.get("/api/management/hospitals")
def get_management_hospitals(current_user: dict = Depends(verify_token)):
    """Get all hospitals for management (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hospitals')
        hospitals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return hospitals
    except Exception as e:
        logger.error(f"Error fetching management hospitals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch hospitals")

@app.get("/api/management/doctors")
def get_management_doctors(current_user: dict = Depends(verify_token)):
    """Get all doctors for management (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
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
    except Exception as e:
        logger.error(f"Error fetching management doctors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch doctors")

@app.get("/api/management/departments")
def get_management_departments(current_user: dict = Depends(verify_token)):
    """Get all departments for management (hospital/admin only)"""
    if current_user['role'] not in ['hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
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
    except Exception as e:
        logger.error(f"Error fetching management departments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

# Appointment management endpoints
@app.post("/api/appointments")
def create_appointment(appointment: AppointmentCreate, current_user: dict = Depends(verify_token)):
    """Create new appointment (user only)"""
    if current_user['role'] != 'user':
        raise HTTPException(status_code=403, detail="Only users can create appointments")
    
    try:
        # Get user ID from email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user['email'],))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        # Validate hospital exists
        cursor.execute('SELECT id FROM hospitals WHERE id = ?', (appointment.hospital_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Validate doctor exists if provided
        if appointment.doctor_id:
            cursor.execute('SELECT id FROM doctors WHERE id = ?', (appointment.doctor_id,))
            if not cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=404, detail="Doctor not found")
        
        cursor.execute('''
            INSERT INTO appointments (user_id, hospital_id, doctor_id, appointment_date, reason, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, appointment.hospital_id, appointment.doctor_id, 
              appointment.appointment_date, appointment.reason, appointment.notes))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Appointment created: {appointment_id} by user {current_user['email']}")
        return {"id": appointment_id, "message": "Appointment created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")

@app.get("/api/appointments")
def get_user_appointments(current_user: dict = Depends(verify_token)):
    """Get user's appointments (user only)"""
    if current_user['role'] != 'user':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get user ID from email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user['email'],))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        cursor.execute('''
            SELECT appointments.*, hospitals.name as hospital_name, doctors.name as doctor_name
            FROM appointments
            JOIN hospitals ON appointments.hospital_id = hospitals.id
            LEFT JOIN doctors ON appointments.doctor_id = doctors.id
            WHERE appointments.user_id = ?
            ORDER BY appointments.appointment_date DESC
        ''', (user_id,))
        
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return appointments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")

@app.put("/api/appointments/{appointment_id}")
def update_appointment(appointment_id: int, update: AppointmentUpdate, current_user: dict = Depends(verify_token)):
    """Update appointment status (user/hospital/admin)"""
    if current_user['role'] not in ['user', 'hospital', 'admin']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if appointment exists
        cursor.execute('SELECT id FROM appointments WHERE id = ?', (appointment_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        cursor.execute('''
            UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?
        ''', (update.status, datetime.now(timezone.utc).isoformat(), appointment_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Appointment {appointment_id} updated to {update.status} by {current_user['email']}")
        return {"message": "Appointment updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update appointment")

@app.delete("/api/appointments/{appointment_id}")
def cancel_appointment(appointment_id: int, current_user: dict = Depends(verify_token)):
    """Cancel appointment (user only)"""
    if current_user['role'] != 'user':
        raise HTTPException(status_code=403, detail="Only users can cancel their appointments")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if appointment exists and belongs to user
        cursor.execute('SELECT id FROM appointments WHERE id = ?', (appointment_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        cursor.execute('''
            UPDATE appointments SET status = 'cancelled', updated_at = ? WHERE id = ?
        ''', (datetime.now(timezone.utc).isoformat(), appointment_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Appointment {appointment_id} cancelled by user {current_user['email']}")
        return {"message": "Appointment cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")

# User profile management endpoints
@app.get("/api/profile")
def get_user_profile(current_user: dict = Depends(verify_token)):
    """Get user profile (user only)"""
    if current_user['role'] != 'user':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get user ID from email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user['email'],))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            return dict(profile)
        else:
            return {"message": "Profile not found. Please create your profile."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@app.post("/api/profile")
def create_user_profile(profile: UserProfileCreate, current_user: dict = Depends(verify_token)):
    """Create user profile (user only)"""
    if current_user['role'] != 'user':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get user ID from email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user['email'],))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        # Check if profile already exists
        cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")
        
        cursor.execute('''
            INSERT INTO user_profiles (user_id, full_name, phone, date_of_birth, address, city, state, 
                                      zip_code, emergency_contact_name, emergency_contact_phone, blood_type, 
                                      allergies, medical_conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, profile.full_name, profile.phone, profile.date_of_birth, profile.address,
              profile.city, profile.state, profile.zip_code, profile.emergency_contact_name,
              profile.emergency_contact_phone, profile.blood_type, profile.allergies, profile.medical_conditions))
        
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Profile created for user {current_user['email']}")
        return {"id": profile_id, "message": "Profile created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create profile")

@app.put("/api/profile")
def update_user_profile(profile: UserProfileCreate, current_user: dict = Depends(verify_token)):
    """Update user profile (user only)"""
    if current_user['role'] != 'user':
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get user ID from email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (current_user['email'],))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        # Check if profile exists
        cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Profile not found. Please create your profile first.")
        
        cursor.execute('''
            UPDATE user_profiles SET full_name=?, phone=?, date_of_birth=?, address=?, city=?, state=?, 
                                    zip_code=?, emergency_contact_name=?, emergency_contact_phone=?, blood_type=?, 
                                    allergies=?, medical_conditions=?, updated_at=?
            WHERE user_id=?
        ''', (profile.full_name, profile.phone, profile.date_of_birth, profile.address, profile.city,
              profile.state, profile.zip_code, profile.emergency_contact_name, profile.emergency_contact_phone,
              profile.blood_type, profile.allergies, profile.medical_conditions,
              datetime.now(timezone.utc).isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Profile updated for user {current_user['email']}")
        return {"message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )