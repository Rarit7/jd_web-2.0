# CLAUDE.md

This file provides comprehensive guidance for Claude Code when working with the chemical industry data aggregation and Telegram monitoring system.

## Project Overview

A sophisticated Flask-based web application that combines chemical industry intelligence gathering, Telegram monitoring, and competitive analysis. The system leverages distributed task processing via Celery and is actively migrating from traditional Jinja2 templates to a modern Vue.js SPA frontend.

**Core Capabilities:**
- Multi-platform chemical data scraping (7+ specialized scrapers)
- Real-time Telegram group monitoring and chat history analysis
- Automated competitive intelligence gathering
- Role-based access control (RBAC) with user management
- Distributed task scheduling and processing

## Quick Start Commands

### Development Environment Setup
```bash
# Complete system startup (recommended for development)
bash start.sh -a

# Stop all services cleanly
bash stop.sh

# Frontend development server
cd frontend && npm install && npm run dev

# Initialize Telegram integration (required on first setup)
python -m scripts.job init_tg

# Database initialization
bash scripts/init_database.sh

# Create conda environment
bash scripts/setup_conda_env.sh
```

### Service Management
```bash
# Selective service startup
bash start.sh -w    # Web server only (Flask app on port 8981)
bash start.sh -c    # Celery workers only

# Manual service control
python web.py                                              # Flask application
celery -A scripts.worker:celery worker -Q jd.celery.first -c 6    # Data processing queue
celery -A scripts.worker:celery worker -Q jd.celery.telegram -c 1  # Telegram operations
celery -A scripts.worker:celery beat                       # Task scheduler

# Frontend development
cd frontend && npm run dev                                 # Vue.js dev server (port 8930)
```

### Common Development Tasks
```bash
# Database operations
python -m utils.insert_dml_data      # Insert test data
python -m utils.delete_chat_history  # Clean chat history

# Job execution
python -m jd.jobs.init_roles_users   # Initialize user roles
python -m jd.jobs.job_queue_manager  # Queue management

# Testing
pytest                               # Run test suite
python jd/tasks/test_base_task.py   # Test base task functionality
```

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Client Layer (Browser)                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│            Frontend (Vue.js 3 + TypeScript)                    │
│              Element Plus UI + Vite (port 8930)                │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST APIs
┌─────────────────────────────┴───────────────────────────────────┐
│               Backend (Flask + SQLAlchemy)                     │
│                    API Server (port 8981)                      │
└─────────────┬─────────────────────────────┬───────────────────┘
              │                             │
┌─────────────┴──────────────┐   ┌──────────┴──────────────────┐
│     Celery Workers         │   │      Database Layer         │
│  - jd.celery.first (6)     │   │    MySQL + Redis Cache      │
│  - jd.celery.telegram (1)  │   │                             │
└────────────────────────────┘   └─────────────────────────────┘
```

### Directory Structure
```
jd_web/
├── web.py                      # Flask application entry point
├── config.py                   # Application configuration
├── start.sh / stop.sh          # Service management scripts
├── requirements.txt            # Python dependencies
├── package.json               # Node.js dependencies
│
├── jd/                        # Main backend application
│   ├── __init__.py            # Flask app factory with auto-blueprint loading
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── tg_group.py        # Telegram group management
│   │   ├── tg_account.py      # Telegram account management
│   │   ├── secure_user.py     # User authentication
│   │   └── ...                # Other domain models
│   ├── services/              # Business logic layer (NO database commits)
│   │   └── spider/            # Web scraping services
│   ├── views/api/             # RESTful API endpoints
│   │   ├── tg/                # Telegram-related APIs
│   │   ├── user/              # User management APIs
│   │   └── ...                # Other API modules
│   ├── jobs/                  # Standalone job scripts
│   │   ├── tg_*.py            # Telegram operation scripts
│   │   └── init_*.py          # Initialization scripts
│   └── tasks/                 # Celery task definitions
│       ├── telegram/          # Telegram processing tasks
│       └── first/             # Data processing tasks
│
├── frontend/                  # Vue.js SPA application
│   ├── src/
│   │   ├── views/             # Page-level components
│   │   ├── components/        # Reusable UI components
│   │   ├── api/               # HTTP client services
│   │   ├── store/             # Pinia state management
│   │   └── router/            # Vue Router configuration
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite build configuration
│
├── scripts/                   # Utility scripts and job runners
├── tests/                     # Test suite
├── utils/                     # Utility scripts
└── dbrt/                      # Database schema (DDL/DML)
```

## Core Features & Components

### Data Processing Pipeline
- **Chemical Intelligence**:
  - Multi-platform scrapers (Baidu, ChemicalBook, Molbase, 1688, etc.)
  - Automated product data collection and analysis
  - Competitive pricing intelligence
  - Market trend analysis

- **Telegram Integration**:
  - Real-time group monitoring and user activity tracking
  - Chat history collection and analysis
  - File download and processing
  - User information extraction and management

- **Task Queue System**:
  - `jd.celery.first`: Heavy data processing (6 concurrent workers)
  - `jd.celery.telegram`: Telegram operations (1 worker for rate limiting)
  - Celery Beat: Automated task scheduling

### Frontend Architecture (Vue.js 3)
- **Modern Stack**: Composition API with TypeScript for type safety
- **UI Framework**: Element Plus for consistent, professional interface
- **Build System**: Vite for fast development and optimized builds
- **Routing**: Vue Router with lazy-loaded components
- **State Management**: Pinia for global application state
- **HTTP Client**: Axios with centralized API configuration

### Authentication & Security
- **Multi-tier Auth**: Session-based with optional JWT support
- **RBAC System**: Role-based access control with granular permissions
- **API Protection**: Custom `ApiBlueprint` with automatic authentication
- **Secure Configuration**: Encrypted database connections and secure defaults

## Development Guidelines

### API Standards & Conventions
```json
// Standard API response format
{
  "err_code": 0,           // 0 = success, >0 = application error
  "err_msg": "",           // Human-readable error message
  "payload": {             // Response data
    "data": [],            // Main data array/object  
    "total": 100,          // Total count for pagination
    "page": 1,             // Current page
    "page_size": 20        // Items per page
  }
}

// HTTP status code usage:
// 200: Success (always check err_code for application errors)
// 400: Bad request / Validation errors
// 401: Authentication required
// 403: Permission denied  
// 404: Resource not found
// 500: Internal server error
```

### Code Organization & Architecture Rules

#### Layer Responsibilities
- **Models** (`jd/models/`): Database entities, relationships, and basic serialization
- **Services** (`jd/services/`): Pure business logic, stateless operations (**NO database commits**)
- **Views** (`jd/views/api/`): API endpoints, request/response handling, authentication
- **Tasks** (`jd/tasks/`): Celery background processing with database commits
- **Jobs** (`jd/jobs/`): Standalone scripts for manual/scheduled execution

#### Database Transaction Rules
```python
# ✅ ALLOWED - Views, Tasks, Jobs can commit
@api_bp.route('/api/users', methods=['POST'])
def create_user():
    user = User(**data)
    db.session.add(user)
    db.session.commit()  # OK in views

# ❌ FORBIDDEN - Services cannot commit
class UserService:
    def create_user(self, data):
        user = User(**data)
        db.session.add(user)
        # db.session.commit()  # NOT ALLOWED in services
        return user
```

#### Model Conventions
```python
# Use built-in to_dict() for JSON serialization
class TgGroup(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# API usage
return jsonify({
    'err_code': 0,
    'payload': {'data': [group.to_dict() for group in groups]}
})
```

### Testing & Quality Assurance
```bash
# Run test suite
pytest tests/

# Test specific modules  
python jd/tasks/test_base_task.py

# Check code quality (if configured)
flake8 jd/
pylint jd/
```

## Environment Configuration

### Runtime Requirements
- **Python**: 3.7+ with Conda environment `sdweb`
- **Node.js**: Latest LTS for frontend development
- **Database**: MySQL 8.0+ with encrypted connections
- **Cache/Message Broker**: Redis 6.0+ for Celery and sessions
- **System**: Linux/macOS recommended for development

### External Service Dependencies
- **Telegram API**: 
  - Requires `api_id` and `api_hash` from https://my.telegram.org
  - Session files stored locally for persistent connections
- **Chemical Platform APIs**: Various vendor integrations
- **Proxy Services**: OxyLabs for web scraping (optional)
- **Task Scheduling**: Celery Beat for automated operations

### Configuration Management
```python
# config.py structure
class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://...'
    
    # Redis
    REDIS_URL = 'redis://localhost:6379/0'
    
    # Telegram
    TG_API_ID = 'your_api_id'
    TG_API_HASH = 'your_api_hash'
    
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
```

### Development Workflow
1. **Environment Setup**: Use provided setup scripts for consistent development environment
2. **Dual Server Development**: Run both frontend (8930) and backend (8981) simultaneously
3. **Database Migrations**: Manual SQL scripts in `dbrt/` directory
4. **Task Processing**: Heavy operations handled by background Celery workers
5. **Legacy Migration**: Gradual replacement of Jinja2 templates with Vue.js components

## Technology Stack

### Backend Technologies
- **Web Framework**: Flask 2.2.5 with SQLAlchemy 2.0.31 ORM
- **Task Queue**: Celery 5.2.7 with Redis 4.5.1 broker
- **Telegram Client**: Telethon 1.36.0 for API interactions
- **Web Automation**: Selenium 4.11.2 for dynamic content scraping
- **Database**: MySQL with PyMySQL connector
- **Authentication**: Flask-Session with Redis backend

### Frontend Technologies
- **Framework**: Vue.js 3 with Composition API
- **Language**: TypeScript for enhanced developer experience
- **UI Library**: Element Plus for consistent component design
- **Build Tool**: Vite for fast development and optimized builds
- **Routing**: Vue Router for SPA navigation
- **State Management**: Pinia as modern Vuex alternative
- **HTTP Client**: Axios with request/response interceptors

### Operational & Monitoring
- **Task Scheduling**: Celery Beat with crontab-style scheduling
- **Logging**: Python logging with configurable levels
- **Process Management**: Custom shell scripts for service lifecycle
- **Development Tools**: Hot reload, source maps, TypeScript checking

### Scheduled Operations
- **Daily (00:00)**: Chemical platform data collection and analysis
- **Every 10 minutes**: Telegram chat history updates and user tracking
- **Hourly**: File processing, cleanup, and system maintenance
- **On-demand**: Manual job execution via CLI scripts

## Critical Operational Notes

### Database & Transaction Management
- **Strict Layer Separation**: Only views, tasks, and jobs may commit database transactions
- **Service Layer Isolation**: Services provide pure business logic without side effects
- **Model Serialization**: Use built-in `to_dict()` methods for consistent JSON output

### Celery & Background Processing  
- **Queue Isolation**: Separate queues for different operation types to prevent blocking
- **Worker Configuration**: Different concurrency levels based on operation characteristics
- **Dependency Resolution**: Some Celery packages may require separate installation steps

### Telegram Integration
- **Session Management**: Telegram sessions must be initialized before first use
- **Rate Limiting**: Single worker for Telegram operations to respect API limits
- **File Handling**: Automatic download and processing of media files

### Development Environment
- **Port Management**: Frontend (8930) and backend (8981) run on different ports
- **Hot Reload**: Both servers support automatic restart on code changes  
- **Architecture Migration**: System gradually transitioning from SSR to SPA model

### Security Considerations
- **API Authentication**: All endpoints protected via custom blueprint authentication
- **Database Security**: Encrypted connections and parameterized queries
- **Session Management**: Secure session handling with Redis backend
- **Configuration**: Sensitive values stored in environment-specific config files