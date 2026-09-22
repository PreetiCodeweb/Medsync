"""
Database setup and migration utilities for MedSync
Supports both SQLite and PostgreSQL databases
"""
import os
import sqlite3
import psycopg2
from psycopg2 import sql
from config import settings

def setup_postgresql_database():
    """Setup PostgreSQL database for production use"""
    if not settings.POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD environment variable must be set for PostgreSQL")
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database='postgres'  # Connect to default database first
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"),
            [settings.POSTGRES_DB]
        )
        if not cursor.fetchone():
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings.POSTGRES_DB)
                )
            )
            print(f"Database {settings.POSTGRES_DB} created successfully")
        
        cursor.close()
        conn.close()
        
        # Connect to the new database
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create tables
        create_tables_postgresql(cursor)
        
        cursor.close()
        conn.close()
        
        print("PostgreSQL database setup completed successfully")
        
    except Exception as e:
        print(f"Error setting up PostgreSQL database: {str(e)}")
        raise

def create_tables_postgresql(cursor):
    """Create all tables in PostgreSQL"""
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL CHECK(role IN ('user', 'hospital', 'admin')),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            address VARCHAR(500) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(255),
            latitude REAL,
            longitude REAL,
            emergency_beds INTEGER DEFAULT 0,
            icu_beds INTEGER DEFAULT 0,
            total_beds INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id SERIAL PRIMARY KEY,
            hospital_id INTEGER REFERENCES hospitals(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            department VARCHAR(100) NOT NULL,
            specialization VARCHAR(200),
            phone VARCHAR(50),
            email VARCHAR(255),
            available BOOLEAN DEFAULT TRUE,
            license_number VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            hospital_id INTEGER REFERENCES hospitals(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Audit logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            action VARCHAR(100) NOT NULL,
            table_name VARCHAR(100),
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            hospital_id INTEGER REFERENCES hospitals(id) ON DELETE CASCADE,
            doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
            appointment_date TIMESTAMP NOT NULL,
            reason TEXT,
            status VARCHAR(50) DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'confirmed', 'completed', 'cancelled')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            full_name VARCHAR(200),
            phone VARCHAR(50),
            date_of_birth DATE,
            address VARCHAR(500),
            city VARCHAR(100),
            state VARCHAR(100),
            zip_code VARCHAR(20),
            emergency_contact_name VARCHAR(200),
            emergency_contact_phone VARCHAR(50),
            blood_type VARCHAR(5),
            allergies TEXT,
            medical_conditions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_hospital_id ON appointments(hospital_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_doctors_hospital_id ON doctors(hospital_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_departments_hospital_id ON departments(hospital_id)')

def seed_demo_data_postgresql(cursor):
    """Seed demo data for PostgreSQL"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Seed default users
    hashed_password = pwd_context.hash("user123")
    cursor.execute('''
        INSERT INTO users (email, password, role) 
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    ''', ('user@medsync.com', hashed_password, 'user'))
    
    hashed_password = pwd_context.hash("hospital123")
    cursor.execute('''
        INSERT INTO users (email, password, role) 
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    ''', ('hospital@medsync.com', hashed_password, 'hospital'))
    
    hashed_password = pwd_context.hash("admin123")
    cursor.execute('''
        INSERT INTO users (email, password, role) 
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    ''', ('admin@medsync.com', hashed_password, 'admin'))
    
    # Seed sample hospitals
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    ''', ('City General Hospital', '123 Main St', '555-0100', 'info@citygeneral.com', 
          40.7128, -74.0060, 5, 3, 50))
    
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    ''', ('St. Mary Medical Center', '456 Oak Ave', '555-0101', 'info@stmary.com', 
          40.7138, -74.0070, 8, 5, 75))
    
    cursor.execute('''
        INSERT INTO hospitals (name, address, phone, email, latitude, longitude, emergency_beds, icu_beds, total_beds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    ''', ('Metro Health Hospital', '789 Pine Rd', '555-0102', 'info@metrohealth.com', 
          40.7148, -74.0080, 3, 2, 30))
    
    print("Demo data seeded successfully")

if __name__ == "__main__":
    if settings.DATABASE_URL.startswith("postgresql"):
        setup_postgresql_database()
    else:
        print("Using SQLite database. No PostgreSQL setup needed.")