# MedSync - AI Hospital Management System

A simplified hospital management system with AI integration for users and hospital management portals.

## Features

### User Portal
- Find nearby hospitals with available emergency/ICU beds
- View available doctors with specializations
- AI voice integration for symptom analysis
- Emergency ambulance button
- Location-based hospital search

### Hospital Management Portal
- Manage hospital information
- Add/update doctor profiles and specializations
- Update bed availability
- Manage hospital departments

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: HTML, CSS, JavaScript (minimal React)
- **Database**: SQLite (simple setup)
- **AI Integration**: Voice-based symptom analysis with RAG system

## Quick Start

### Option 1: Automated Startup
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Startup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

#### Frontend Setup
```bash
cd frontend
# Simple static file serving
python3 -m http.server 3000
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Credentials

### User Portal
- Email: user@medsync.com
- Password: user123

### Hospital Portal
- Email: hospital@medsync.com
- Password: hospital123

## Project Structure
```
medsync/
├── backend/
│   ├── app.py              # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── venv/              # Python virtual environment
│   └── database.db        # SQLite database (auto-created)
├── frontend/
│   ├── index.html          # Login page
│   ├── user_portal.html    # User interface
│   ├── hospital_portal.html # Hospital management interface
│   ├── styles.css          # Global styles
│   └── script.js           # Frontend logic
├── start.sh               # Automated startup script
└── README.md             # This file
```

## API Endpoints

### Authentication
- `POST /api/login` - User login

### Public Endpoints
- `GET /api/hospitals` - Get all hospitals
- `GET /api/hospitals/{id}/doctors` - Get doctors for a hospital
- `GET /api/hospitals/{id}/departments` - Get departments for a hospital
- `POST /api/ai/symptom-analysis` - AI symptom analysis

### Hospital Management (Requires Authentication)
- `GET /api/management/hospitals` - Get all hospitals (management view)
- `GET /api/management/doctors` - Get all doctors (management view)
- `GET /api/management/departments` - Get all departments (management view)
- `POST /api/hospitals` - Create hospital
- `PUT /api/hospitals/{id}` - Update hospital
- `POST /api/doctors` - Create doctor
- `PUT /api/doctors/{id}` - Update doctor
- `DELETE /api/doctors/{id}` - Delete doctor
- `POST /api/departments` - Create department

## Features Implementation

### AI Symptom Analysis
The system uses a RAG-based approach for symptom analysis:
- Users can describe symptoms via voice or text
- AI analyzes symptoms and suggests possible conditions
- Recommends appropriate medical departments
- Provides severity assessment
- Offers basic medical guidance

### Voice Integration
- Web Speech API for voice input
- Real-time speech-to-text conversion
- Fallback to text input if voice not supported

### Location Services
- GPS-based location detection
- Manual location input option
- Distance calculation for hospital recommendations

## Development Notes

### Database Schema
- **Users**: Authentication and role management
- **Hospitals**: Hospital information and bed availability
- **Doctors**: Doctor profiles and availability
- **Departments**: Hospital departments and descriptions

### Security Features
- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- CORS protection

### Browser Compatibility
- Modern browsers with ES6+ support
- Chrome/Edge recommended for voice features
- Fallbacks for unsupported features

## Troubleshooting

### Backend Issues
- Ensure Python 3.11+ is installed
- Check that virtual environment is activated
- Verify port 8000 is not in use

### Frontend Issues
- Ensure Python 3 is installed for static server
- Check that port 3000 is not in use
- Clear browser cache if experiencing issues

### Voice Recognition Issues
- Use Chrome or Edge for best voice support
- Check microphone permissions
- Use text input as fallback

## Future Enhancements

- Real doctor appointment booking
- Integration with real hospital systems
- Advanced AI/ML models for diagnosis
- Mobile app development
- Real-time bed availability updates
- Integration with emergency services
