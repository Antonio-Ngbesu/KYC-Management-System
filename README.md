# 🏦 KYC System - Know Your Customer Management Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A comprehensive **Know Your Customer (KYC)** management system built with modern Python technologies. This platform provides secure document processing, verification workflows, and compliance management for financial institutions and businesses requiring customer identity verification.

## ✨ Key Features

### 🔐 **Authentication & Security**

- **Role-Based Access Control** (Customer, Analyst, Admin)
- **JWT Token Authentication** with secure session management
- **Development Authentication System** for easy testing
- **Account Lockout Protection** against brute force attacks

### 📋 **Document Management**

- **Multi-Format Support** (PDF, Images, Scanned Documents)
- **Secure Upload System** with validation and virus scanning
- **Document Versioning** and audit trails
- **Azure Blob Storage Integration** for scalable storage

### 🔍 **KYC Processing**

- **Automated Document Analysis** using AI/ML services
- **Risk Assessment Engine** with configurable rules
- **Compliance Workflow Management**
- **Real-time Status Tracking** for customers

### 📊 **Multi-Interface System**

- **Customer Portal** - Document upload and status tracking
- **Analyst Dashboard** - Review and decision-making interface
- **Admin Dashboard** - System management and configuration
- **Secure System Launcher** - Centralized access control

### 🎨 **Modern UI/UX**

- **Responsive Design** with modern CSS styling
- **Real-time Updates** and notifications
- **Interactive Dashboards** with data visualization
- **Professional Gradient Themes** for each interface

## 🏗️ Architecture

```
KYC System/
├── 🔧 Backend (FastAPI)
│   ├── src/api/           # REST API endpoints
│   ├── src/auth/          # Authentication services
│   ├── src/models/        # Data models & schemas
│   └── src/services/      # Business logic & integrations
├── 🖥️ Frontend (Streamlit)
│   ├── src/ui/customer_portal.py    # Customer interface
│   ├── src/ui/analyst_dashboard.py  # Analyst interface
│   └── src/ui/admin_dashboard.py    # Admin interface
├── 🧪 Testing
│   ├── tests/             # Comprehensive test suite
│   ├── test_*.py          # Integration tests
│   └── debug_*.py         # Development utilities
└── 🚀 Deployment
    ├── secure_launcher.py  # System launcher
    ├── requirements.txt    # Dependencies
    └── README.md          # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **PostgreSQL** (optional - SQLite fallback included)
- **Redis** (optional - for caching)
- **Azure Account** (optional - for cloud storage)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Antonio-Ngbesu/KYC-System---Know-Your-Customer-Management-Platform.git
   cd KYC-System---Know-Your-Customer-Management-Platform
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### 🎯 Running the System

#### Option 1: Secure Launcher (Recommended)

```bash
streamlit run secure_launcher.py --server.port 8520
```

- Navigate to: http://localhost:8520
- Login with demo credentials (see below)
- Launch services from the web interface

#### Option 2: Manual Launch

```bash
# API Server
cd src && python -m uvicorn api.main:app --reload --port 8000

# Customer Portal
streamlit run src/ui/customer_portal.py --server.port 8501

# Analyst Dashboard
streamlit run src/ui/analyst_dashboard.py --server.port 8502

# Admin Dashboard
streamlit run src/ui/admin_dashboard.py --server.port 8503
```

### 🔐 Demo Credentials

| Role         | Username            | Password  | Access Level                        |
| ------------ | ------------------- | --------- | ----------------------------------- |
| **Customer** | `customer@demo.com` | `demo123` | Document upload, status tracking    |
| **Analyst**  | `analyst@demo.com`  | `demo123` | Document review, risk assessment    |
| **Admin**    | `admin@demo.com`    | `demo123` | Full system access, user management |

## 🌐 Access Points

| Service               | URL                        | Description                                |
| --------------------- | -------------------------- | ------------------------------------------ |
| **System Launcher**   | http://localhost:8520      | Secure authentication & service management |
| **Customer Portal**   | http://localhost:8501      | Customer document submission               |
| **Analyst Dashboard** | http://localhost:8502      | KYC review and processing                  |
| **Admin Dashboard**   | http://localhost:8503      | System administration                      |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs (Swagger)             |

## 🧪 Testing

### Run Test Suite

```bash
# All tests
python -m pytest tests/ -v

# Specific test categories
python test_api_health.py           # API health checks
python test_storage.py              # Storage system tests
python test_upload_system.py        # Upload functionality
python test_all_services.py         # End-to-end tests
```

### Development Testing

```bash
# Authentication system
streamlit run auth_test.py --server.port 8510

# Connection debugging
python debug_connection.py

# Working process demo
python demo_working_process.py
```

## 📦 Technology Stack

### **Backend**

- **FastAPI** - High-performance async API framework
- **SQLAlchemy** - Database ORM with async support
- **Alembic** - Database migration management
- **PostgreSQL** - Primary database (SQLite fallback)
- **Redis** - Caching and session storage
- **Uvicorn** - ASGI server

### **Frontend**

- **Streamlit** - Interactive web applications
- **Modern CSS** - Responsive design with gradients
- **JavaScript Integration** - Enhanced interactivity

### **Security & Auth**

- **JWT Tokens** - Secure authentication
- **BCrypt** - Password hashing
- **python-jose** - JWT handling
- **Passlib** - Password utilities

### **Storage & Integration**

- **Azure Blob Storage** - Cloud document storage
- **File Upload Validation** - Security scanning
- **Database Abstraction** - Multi-database support

## 🔒 Security Features

- ✅ **Authentication Required** for all sensitive operations
- ✅ **Role-Based Access Control** with granular permissions
- ✅ **JWT Token Management** with expiration handling
- ✅ **Account Lockout Protection** against brute force
- ✅ **Secure File Upload** with validation and scanning
- ✅ **Audit Logging** for compliance and monitoring
- ✅ **Data Encryption** in transit and at rest
- ✅ **Session Management** with automatic cleanup

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] **Machine Learning Integration** - AI-powered document analysis
- [ ] **Mobile Application** - Native iOS/Android apps
- [ ] **API Rate Limiting** - Enhanced security controls
- [ ] **Advanced Analytics** - Business intelligence dashboard
- [ ] **Multi-tenant Support** - SaaS deployment options
- [ ] **Blockchain Integration** - Immutable audit trails
- [ ] **Advanced Reporting** - Compliance and regulatory reports

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join our GitHub Discussions for questions
- **Email**: [support@kyc-system.com](mailto:support@kyc-system.com)

## 🏆 Acknowledgments

- Built with ❤️ using modern Python ecosystem
- Inspired by financial industry best practices
- Community-driven development approach

---

**⭐ Star this repository if you find it helpful!**

![KYC System Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=KYC+System+Demo)
