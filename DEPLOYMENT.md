# MedSync Professional - Deployment Guide

## 🚀 Industry-Ready Deployment

This guide provides comprehensive instructions for deploying MedSync in a production environment.

## 📋 Prerequisites

### Hardware Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB disk space
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB disk space
- **Database**: Additional 10GB for PostgreSQL storage

### Software Requirements
- Docker & Docker Compose (recommended)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if not using Docker)
- Nginx (for production serving)

## 🔧 Environment Configuration

### Production Environment Variables

Create a `.env.production` file with the following variables:

```bash
# Application
APP_NAME=MedSync
APP_VERSION=2.0.0
ENVIRONMENT=production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-very-secure-secret-key-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://medsync:your-secure-password@postgres:5432/medsync
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=medsync
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=medsync

# CORS (Update with your actual domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# RAG System
ENABLE_RAG=true
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO

# Performance
ENABLE_CACHING=true
CACHE_TTL=300
RATE_LIMIT_PER_MINUTE=60
MAX_REQUEST_SIZE=10485760

# Grafana
GRAFANA_PASSWORD=your-grafana-admin-password
```

## 🐳 Docker Deployment (Recommended)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Medsync
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env.production
# Edit .env.production with your production values
```

### 3. Build and Start Services

```bash
# Production deployment with PostgreSQL
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f medsync-backend
```

### 4. Initialize Database

```bash
# The database will be automatically initialized on first startup
# For manual database setup:
docker-compose -f docker-compose.prod.yml exec medsync-backend python database_setup.py
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Frontend
open http://localhost:3000

# Grafana (admin/admin or your configured password)
open http://localhost:3001

# Prometheus
open http://localhost:9091
```

## 🌐 Production Server Setup

### Using Nginx as Reverse Proxy

1. **Install Nginx**
```bash
sudo apt-get update
sudo apt-get install nginx
```

2. **Configure Nginx**
```nginx
# /etc/nginx/sites-available/medsync
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # Metrics (internal access only)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://localhost:8000/metrics;
    }
}
```

3. **Enable Configuration**
```bash
sudo ln -s /etc/nginx/sites-available/medsync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS Configuration with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

## 🔒 Security Hardening

### 1. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Database Security
- Use strong passwords
- Restrict database access to localhost
- Enable SSL connections
- Regular backups

### 3. Application Security
- Keep dependencies updated
- Enable HTTPS only in production
- Regular security audits
- Monitor logs for suspicious activity

## 📊 Monitoring & Alerting

### Prometheus Metrics

Access metrics at: `http://your-domain.com/metrics`

Key metrics to monitor:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `rag_searches_total` - RAG system searches
- `rag_analysis_duration_seconds` - RAG analysis time

### Grafana Dashboards

1. Login to Grafana (default: admin/admin)
2. Add Prometheus as data source
3. Import dashboard from MedSync repository
4. Set up alerts for:
   - High error rates
   - Slow response times
   - Database connection issues
   - RAG system failures

### Log Monitoring

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f medsync-backend

# Set up log rotation
# Configure in docker-compose.yml with log drivers
```

## 🔄 CI/CD Pipeline

The included GitHub Actions workflow handles:

1. **Testing**: Automated test execution
2. **Security Scanning**: Trivy vulnerability scanner
3. **Building**: Docker image creation
4. **Deployment**: Push to Docker registry

Configure secrets in GitHub:
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
- `POSTGRES_PASSWORD` - Database password
- `SECRET_KEY` - Application secret key
- `GRAFANA_PASSWORD` - Grafana admin password

## 📈 Scaling Strategies

### Horizontal Scaling

```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale medsync-backend=3

# Configure load balancing in Nginx
upstream medsync_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

### Database Scaling

- **Read Replicas**: Set up PostgreSQL read replicas
- **Connection Pooling**: Use PgBouncer for connection management
- **Caching**: Implement Redis for caching

### Performance Optimization

1. **Enable Caching**
```bash
# In .env.production
ENABLE_CACHING=true
CACHE_TTL=300
```

2. **Database Indexing**
- Ensure proper indexes on frequently queried columns
- Monitor query performance

3. **Static Asset Optimization**
- Use CDN for static files
- Enable gzip compression

## 🚨 Backup & Recovery

### Database Backups

```bash
# Automated daily backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U medsync medsync > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U medsync medsync < backup_20260922.sql
```

### RAG System Backups

```bash
# Backup ChromaDB
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz backend/chroma_db/

# Restore
tar -xzf chroma_backup_20260922.tar.gz
```

## 🧪 Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database backups configured
- [ ] Monitoring dashboards set up
- [ ] Error tracking configured
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Backup and recovery tested
- [ ] Documentation updated
- [ ] Team trained on operations

## 🐛 Troubleshooting

### Common Issues

**Application won't start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs medsync-backend

# Check port conflicts
sudo netstat -tulpn | grep :8000
```

**Database connection errors**
```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec medsync-backend python -c "from config import settings; print(settings.DATABASE_URL)"
```

**RAG system not working**
```bash
# Check ChromaDB directory
ls -la backend/chroma_db/

# Verify model installation
docker-compose -f docker-compose.prod.yml exec medsync-backend python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## 📞 Support

For production support:
- Email: support@medsync.com
- Documentation: https://docs.medsync.com
- GitHub Issues: https://github.com/your-repo/issues

## 🔄 Updates & Maintenance

### Rolling Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Zero-downtime deployment
docker-compose -f docker-compose.prod.yml up -d --no-deps --build medsync-backend
```

### Dependency Updates

```bash
# Update Python dependencies
cd backend
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

**MedSync Professional v2.0.0** - Industry-Deployed Hospital Management System