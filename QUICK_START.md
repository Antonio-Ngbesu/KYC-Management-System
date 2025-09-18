# KYC Document Analyzer System - Quick Start Guide

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

```bash
# Start all services with monitoring
python start_system.py start

# Check system status
python start_system.py status

# Stop all services
python start_system.py stop
```

### Option 2: Manual Launch

```bash
# 1. Start API Server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Launch System Launcher (in new terminal)
streamlit run src/ui/system_launcher.py --server.port 8504

# 3. Open browser and navigate to http://localhost:8504
```

## 🌐 Service URLs

| Service               | URL                        | Purpose               |
| --------------------- | -------------------------- | --------------------- |
| **System Launcher**   | http://localhost:8504      | Main system hub       |
| **API Server**        | http://localhost:8000      | Backend API           |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs  |
| **Customer Portal**   | http://localhost:8501      | Customer interface    |
| **Analyst Dashboard** | http://localhost:8502      | KYC analyst tools     |
| **Admin Dashboard**   | http://localhost:8503      | System administration |
| **Integration Tests** | http://localhost:8505      | System testing suite  |

## 🏗️ System Architecture

### Core Components

- **FastAPI Backend**: RESTful API with real-time WebSocket support
- **Streamlit Frontend**: Multiple specialized user interfaces
- **PostgreSQL Database**: Secure data storage with audit logging
- **Azure AI Services**: Document analysis and identity verification
- **Azure Blob Storage**: Secure document storage with retention policies

### User Interfaces

1. **Customer Portal** (`src/ui/customer_portal.py`)

   - Document upload with drag-and-drop
   - Real-time KYC status tracking
   - Risk assessment display
   - Profile management

2. **Analyst Dashboard** (`src/ui/analyst_dashboard.py`)

   - Review queue management
   - Document analysis tools
   - Risk scoring interface
   - Decision workflows

3. **Admin Dashboard** (`src/ui/admin_dashboard.py`)

   - System monitoring
   - User management
   - Configuration controls
   - Audit logs and alerts

4. **System Launcher** (`src/ui/system_launcher.py`)
   - Unified interface hub
   - Service management
   - System status monitoring
   - Quick actions

## 🔧 Development Commands

### System Management

```bash
# Start system with monitoring
python start_system.py start

# Check all service status
python start_system.py status

# Restart specific service
python start_system.py restart --service api
python start_system.py restart --service customer

# Monitor services (auto-restart on failure)
python start_system.py monitor --monitor-interval 30
```

### Individual Services

```bash
# API Server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Customer Portal
streamlit run src/ui/customer_portal.py --server.port 8501

# Analyst Dashboard
streamlit run src/ui/analyst_dashboard.py --server.port 8502

# Admin Dashboard
streamlit run src/ui/admin_dashboard.py --server.port 8503

# System Launcher
streamlit run src/ui/system_launcher.py --server.port 8504

# Integration Tests
streamlit run src/ui/test_integration.py --server.port 8505
```

### Testing

```bash
# Run comprehensive tests
python -m pytest tests/ -v

# Test specific components
python test_api_health.py
python test_upload_system.py
python test_storage.py

# Integration testing via UI
# Navigate to http://localhost:8505
```

## 📋 System Requirements

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
set AZURE_STORAGE_CONNECTION_STRING=your_connection_string
set AZURE_COGNITIVE_SERVICES_KEY=your_key
set AZURE_COGNITIVE_SERVICES_ENDPOINT=your_endpoint
set DATABASE_URL=postgresql://user:pass@localhost/kyc_db
```

### Database Setup

```bash
# Initialize PostgreSQL database
# The system will auto-create tables on first run
```

## 🔒 Security Features

### Authentication & Authorization

- Role-based access control (Customer/Analyst/Admin)
- Session management with secure tokens
- Multi-factor authentication support

### Data Protection

- End-to-end encryption for sensitive data
- PII detection and redaction
- Secure document storage with access controls
- Comprehensive audit logging

### Compliance

- GDPR compliance with data retention policies
- SOX compliance with audit trails
- Bank-grade security controls
- Automated compliance reporting

## 📊 Monitoring & Analytics

### System Monitoring

- Real-time performance metrics
- Service health monitoring
- Automated alerting
- Resource usage tracking

### Business Analytics

- KYC processing metrics
- Risk assessment analytics
- User activity dashboards
- Compliance reporting

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**

   ```bash
   # Kill process on specific port (Windows)
   netstat -ano | findstr :8000
   taskkill /PID <process_id> /F

   # Or use system manager
   python start_system.py stop
   ```

2. **API Connection Failed**

   - Ensure API server is running on port 8000
   - Check database connection
   - Verify environment variables

3. **File Upload Issues**

   - Check Azure Storage connection
   - Verify file size limits
   - Ensure proper permissions

4. **UI Not Loading**
   - Clear browser cache
   - Check console for JavaScript errors
   - Verify Streamlit is running

### Log Files

- API logs: Check terminal output or configure file logging
- UI logs: Available in Streamlit interface
- System logs: Via system manager monitoring

## 🚀 Production Deployment

### Docker Deployment (Coming in Phase 5)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale api=2 --scale worker=3
```

### Cloud Deployment

- Azure App Service for API
- Azure Static Web Apps for UI
- Azure Database for PostgreSQL
- Azure Blob Storage for documents
- Azure Monitor for logging

## 📚 API Documentation

### Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `POST /customers` - Register new customer
- `POST /upload` - Upload documents
- `GET /applications/{id}` - Get application status
- `POST /analyze` - Trigger document analysis
- `WebSocket /ws/notifications` - Real-time notifications

## 🤝 Support

### Getting Help

1. Check this README for common solutions
2. Review API documentation at `/docs`
3. Run integration tests to identify issues
4. Check system status via launcher interface

### Development Workflow

1. Use System Launcher for unified access
2. Run integration tests after changes
3. Monitor system health during development
4. Use individual service commands for debugging

---

**KYC Document Analyzer v2.0.0** - Production-Ready Banking Solution  
Built with FastAPI, Streamlit, Azure AI Services, and PostgreSQL
