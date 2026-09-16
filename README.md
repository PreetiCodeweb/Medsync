# MedSync - AI Hospital Management System

## 🏥 Overview

MedSync is a professional hospital management system with advanced AI capabilities, featuring a production-ready RAG (Retrieval-Augmented Generation) system for intelligent medical analysis and search.

## 🌟 Version Information

- **Current Version**: 2.0.0 (Professional)
- **Status**: Production Ready
- **RAG System**: ✅ Enabled with ChromaDB
- **Monitoring**: ✅ Prometheus & Grafana integrated

## 📚 Documentation

- **Quick Start**: See below for basic setup
- **Professional Guide**: See [PROFESSIONAL_README.md](PROFESSIONAL_README.md) for enterprise deployment
- **API Documentation**: Available at `/docs` when running

## ✨ Key Features

### 🧠 Advanced RAG System
- **Vector Database**: ChromaDB for efficient semantic search
- **Embedding Model**: Sentence Transformers for medical text understanding
- **Document Processing**: Intelligent chunking and indexing
- **Semantic Search**: Context-aware medical knowledge retrieval
- **Confidence Scoring**: Quantified analysis reliability

### 🔒 Enterprise Security
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Granular permissions (user, hospital, admin)
- **Password Hashing**: Bcrypt encryption
- **CORS Protection**: Configurable cross-origin policies
- **Audit Logging**: Comprehensive activity tracking

### 📊 Professional Monitoring
- **Prometheus Metrics**: Real-time performance monitoring
- **Grafana Dashboards**: Visual analytics
- **Health Checks**: Automated system health monitoring
- **Structured Logging**: JSON-formatted logs for analysis

### 🚀 Production Ready
- **Docker Support**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Nginx Integration**: Professional reverse proxy
- **Environment Configuration**: Flexible settings management

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended for Production)

```bash
# Clone repository
git clone <repository-url>
cd Medsync

# Configure environment
cp backend/.env.example backend/.env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Access services
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Grafana: http://localhost:3001 (admin/admin)
# Prometheus: http://localhost:9091
```

### Option 2: Local Development

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py

# Frontend setup (new terminal)
cd frontend
python3 -m http.server 3000
```

### Option 3: Simple Startup Script

```bash
chmod +x start.sh
./start.sh
```

## 🔐 Default Credentials

### User Portal
- Email: `user@medsync.com`
- Password: `user123`

### Hospital Portal
- Email: `hospital@medsync.com`
- Password: `hospital123`

### Admin Portal
- Email: `admin@medsync.com`
- Password: `admin123`

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Grafana**: http://localhost:3001 (Docker deployment)
- **Prometheus**: http://localhost:9091 (Docker deployment)

## 🏗️ Project Structure

```
medsync/
├── backend/
│   ├── app.py                 # Main FastAPI application
│   ├── config.py              # Professional configuration management
│   ├── rag_system.py          # RAG system implementation
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment configuration template
│   ├── venv/                 # Python virtual environment
│   ├── database.db           # SQLite database (auto-created)
│   └── chroma_db/            # Vector database (auto-created)
├── frontend/
│   ├── index.html            # Login page
│   ├── user_portal.html      # User interface with RAG features
│   ├── hospital_portal.html  # Hospital management interface
│   ├── styles.css            # Enhanced styling
│   └── script.js             # Frontend logic with RAG integration
├── docker-compose.yml        # Multi-service orchestration
├── Dockerfile               # Backend container definition
├── nginx.conf               # Nginx configuration
├── prometheus.yml           # Prometheus configuration
├── start.sh                 # Simple startup script
├── README.md               # This file
└── PROFESSIONAL_README.md  # Enterprise deployment guide
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `backend/.env`:

```bash
# RAG System
ENABLE_RAG=true              # Enable/disable RAG system
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHUNK_SIZE=500
TOP_K_RESULTS=5

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO
```

## 📡 API Endpoints

### System
- `GET /` - System information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Interactive API documentation

### Authentication
- `POST /api/login` - User authentication

### Public API
- `GET /api/hospitals` - List all hospitals
- `GET /api/hospitals/{id}/doctors` - Get hospital doctors
- `GET /api/hospitals/{id}/departments` - Get hospital departments
- `POST /api/ai/symptom-analysis` - AI symptom analysis (RAG-powered)
- `POST /api/ai/search` - Direct RAG search

### Management API (Authenticated)
- `GET /api/management/hospitals` - Manage hospitals
- `GET /api/management/doctors` - Manage doctors
- `GET /api/management/departments` - Manage departments
- CRUD operations for hospitals, doctors, and departments

## 🧠 RAG System Features

### Knowledge Base
Pre-loaded with comprehensive medical information:
- Cardiology and cardiovascular conditions
- Neurology and brain disorders
- Pulmonology and respiratory conditions
- Gastroenterology and digestive issues
- Orthopedics and musculoskeletal conditions
- Emergency medicine and critical care
- Pediatrics and child health
- Dermatology and skin conditions

### Advanced Features
- **Semantic Search**: Understands context and meaning
- **Confidence Scoring**: Quantified analysis reliability
- **Source Attribution**: References knowledge base documents
- **Fallback Analysis**: Graceful degradation when RAG is disabled
- **Dynamic Updates**: Expandable knowledge base

## 🔒 Security Features

- **JWT Authentication**: Secure token-based auth
- **Role-Based Access**: User, Hospital, Admin roles
- **Password Encryption**: Bcrypt hashing
- **CORS Protection**: Configurable origins
- **Input Validation**: Comprehensive data validation
- **Error Handling**: Secure error responses

## 📊 Monitoring & Observability

### Metrics Collection
- HTTP request count and duration
- RAG search performance
- System health status
- Custom business metrics

### Logging
- Structured JSON logs
- Configurable log levels
- Request/response logging
- Error tracking

### Health Checks
- Database connectivity
- RAG system status
- Service availability

## 🐳 Docker Deployment

### Services
- **medsync-backend**: FastAPI with RAG system
- **medsync-frontend**: Nginx web server
- **prometheus**: Metrics collection
- **grafana**: Visualization dashboards

### Scaling
```bash
# Scale backend services
docker-compose up -d --scale medsync-backend=3
```

## 🧪 Testing

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Symptom analysis with RAG
curl -X POST http://localhost:8000/api/ai/symptom-analysis \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"chest pain and shortness of breath","include_rag":true}'

# Direct RAG search
curl -X POST http://localhost:8000/api/ai/search \
  -H "Content-Type: application/json" \
  -d '{"query":"heart attack symptoms","top_k":3}'
```

## 🚨 Troubleshooting

### Common Issues

**RAG System Not Working**
```bash
# Check ChromaDB directory
ls -la backend/chroma_db

# Verify embedding model installation
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Database Connection Issues**
```bash
# Check database file permissions
ls -la backend/database.db
chmod 644 backend/database.db
```

**Performance Issues**
```bash
# Check metrics
curl http://localhost:8000/metrics

# View application logs
docker-compose logs medsync-backend
```

## 📈 Performance Optimization

- **Database**: Indexed queries, connection pooling
- **RAG System**: Embedding caching, batch processing
- **Caching**: API response caching, static asset optimization
- **Load Balancing**: Nginx configuration for scaling

## 🔄 CI/CD

### GitHub Actions
```yaml
# Automated testing and deployment
# See PROFESSIONAL_README.md for complete CI/CD setup
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

Proprietary - All rights reserved

## 🏆 Professional Features

This is the **Professional Edition** with:
- ✅ Production-ready RAG system
- ✅ Enterprise security
- ✅ Professional monitoring
- ✅ Docker deployment
- ✅ Scalable architecture
- ✅ Comprehensive documentation

For detailed enterprise deployment instructions, see [PROFESSIONAL_README.md](PROFESSIONAL_README.md).
