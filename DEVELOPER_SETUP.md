# Budget Pulse - Developer Setup Guide

Complete guide for setting up Budget Pulse development environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Running Tests](#running-tests)
8. [Development Workflow](#development-workflow)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **PostgreSQL** (for production) - [Download](https://www.postgresql.org/download/)
- **Code Editor** - VS Code, PyCharm, or similar

### Optional Tools

- **Docker** - For containerized deployment
- **Postman** - For API testing
- **Node.js** - For frontend build tools (Tailwind CSS)

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/TurtleWithGlasses/expense-manager-web-app.git
cd expense-manager-web-app

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
python run_local.py
```

Visit http://localhost:8000

---

## Detailed Setup

### 1. Clone Repository

```bash
git clone https://github.com/TurtleWithGlasses/expense-manager-web-app.git
cd expense-manager-web-app
```

---

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Verify activation:**
```bash
which python  # Should show .venv path
```

---

### 3. Install Dependencies

```bash
# Install all packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Key Dependencies:**
- FastAPI - Web framework
- SQLAlchemy - ORM
- Uvicorn - ASGI server
- Alembic - Database migrations
- scikit-learn - Machine Learning
- Pandas - Data analysis
- openpyxl - Excel export
- ReportLab - PDF generation

---

### 4. Environment Variables

Create `.env` file in project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/budgetpulse
# Or use SQLite for development:
# DATABASE_URL=sqlite:///./app.db

# Application Settings
SECRET_KEY=your-secret-key-here-change-in-production
ENV=dev
BASE_URL=http://localhost:8000

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@budgetpulse.com
SMTP_FROM_NAME=Budget Pulse

# Alternative: Resend API
RESEND_API_KEY=your-resend-api-key

# Exchange Rate API (optional)
EXCHANGE_RATE_API_KEY=your-api-key
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Environment Configuration

### Development Environment

The app automatically detects development environment and:
- Uses SQLite database (`app.db`)
- Enables hot reload
- Shows detailed error messages
- Disables report scheduler

### Production Environment

Set `ENV=production` for:
- PostgreSQL database
- Optimized performance
- Error logging only
- Enabled report scheduler
- Security headers

---

## Database Setup

### Using SQLite (Development)

**Automatic setup:**
- No configuration needed
- Database created automatically at `app.db`
- Perfect for local development

### Using PostgreSQL (Production)

**1. Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Mac
brew install postgresql

# Windows
# Download installer from postgresql.org
```

**2. Create Database:**
```bash
# Access PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE budgetpulse;

# Create user (optional)
CREATE USER budgetpulse_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE budgetpulse TO budgetpulse_user;
```

**3. Update `.env`:**
```
DATABASE_URL=postgresql://budgetpulse_user:secure_password@localhost:5432/budgetpulse
```

---

### Database Migrations

**Apply migrations:**
```bash
alembic upgrade head
```

**Create new migration:**
```bash
alembic revision -m "description_of_changes"
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

---

## Running the Application

### Development Server

**Method 1: Using run_local.py (Recommended)**
```bash
python run_local.py
```

**Method 2: Using Uvicorn directly**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Method 3: Using Gunicorn (Production-like)**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Access the Application

- **Local:** http://localhost:8000
- **Network:** http://YOUR_IP:8000

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_ai_services.py
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

**View coverage report:**
```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

### Run Performance Tests Only

```bash
pytest -m performance
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit files in your code editor.

### 3. Run Tests

```bash
pytest
```

### 4. Check Code Quality

```bash
# Format code (if using black)
black app/

# Check linting (if using flake8)
flake8 app/

# Type checking (if using mypy)
mypy app/
```

### 5. Commit Changes

```bash
git add .
git commit -m "Descriptive commit message"
```

### 6. Push to GitHub

```bash
git push origin feature/your-feature-name
```

### 7. Create Pull Request

- Go to GitHub repository
- Click "New Pull Request"
- Select your branch
- Add description
- Request review

---

## Project Structure

```
expense-manager-web-app/
├── app/
│   ├── api/                    # API routes and endpoints
│   │   └── v1/                # Version 1 endpoints
│   │       ├── entries.py     # Entry endpoints
│   │       ├── dashboard.py   # Dashboard endpoints
│   │       ├── ai.py          # AI endpoints
│   │       └── reports.py     # Report endpoints
│   ├── core/                   # Core configuration
│   │   ├── config.py          # App configuration
│   │   ├── security.py        # Security utilities
│   │   ├── session.py         # Session management
│   │   └── currency.py        # Currency service
│   ├── db/                     # Database configuration
│   │   ├── base.py            # Base model class
│   │   ├── engine.py          # Database engine
│   │   └── session.py         # Session factory
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py            # User model
│   │   ├── entry.py           # Entry model
│   │   ├── category.py        # Category model
│   │   ├── ai_model.py        # AI model tracking
│   │   └── weekly_report.py   # Report models
│   ├── schemas/                # Pydantic schemas
│   │   ├── entry.py           # Entry schemas
│   │   └── user.py            # User schemas
│   ├── services/               # Business logic
│   │   ├── ai_service.py      # AI service
│   │   ├── entries.py         # Entry service
│   │   ├── weekly_report_service.py
│   │   └── email.py           # Email service
│   ├── ai/                     # AI/ML components
│   │   ├── models/            # ML models
│   │   ├── data/              # Data pipelines
│   │   └── utils/             # AI utilities
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html          # Base template
│   │   ├── dashboard.html     # Dashboard
│   │   ├── entries/           # Entry templates
│   │   ├── reports/           # Report templates
│   │   └── settings/          # Settings templates
│   ├── deps.py                 # FastAPI dependencies
│   └── main.py                 # Application entry point
├── tests/                      # Test suite
│   ├── integration/           # Integration tests
│   ├── performance/           # Performance tests
│   └── test_*.py              # Unit tests
├── static/                     # Static files
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript
├── alembic/                    # Database migrations
│   └── versions/              # Migration files
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── alembic.ini                # Alembic configuration
├── pytest.ini                 # Pytest configuration
└── README.md                  # Project overview
```

---

## Deployment

### Heroku Deployment

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ENV=production

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
```

### Railway Deployment

1. Connect GitHub repository
2. Configure environment variables
3. Add PostgreSQL database
4. Deploy automatically

### Docker Deployment

```bash
# Build image
docker build -t budgetpulse .

# Run container
docker run -p 8000:8000 budgetpulse
```

---

## Development Tips

### Hot Reload

Uvicorn automatically reloads when you save files:
```bash
uvicorn app.main:app --reload
```

### Database Reset

**⚠️ Warning: Deletes all data!**
```bash
python reset_db.py
```

### Debugging

**Enable debug mode:**
```python
# app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use FastAPI docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Code Style Guidelines

### Python Code Style

- **PEP 8** compliance
- **Type hints** for all functions
- **Docstrings** for public methods
- **Async/await** for I/O operations

**Example:**
```python
async def create_entry(
    db: Session,
    user_id: int,
    type: str,
    amount: float
) -> Entry:
    """
    Create a new transaction entry.
    
    Args:
        db: Database session
        user_id: ID of the user
        type: 'income' or 'expense'
        amount: Transaction amount
    
    Returns:
        Created Entry object
    
    Raises:
        ValueError: If amount is negative
    """
    if amount < 0:
        raise ValueError("Amount must be positive")
    
    entry = Entry(user_id=user_id, type=type, amount=amount)
    db.add(entry)
    db.commit()
    return entry
```

---

### HTML/Template Style

- **Semantic HTML5**
- **Bootstrap 5** classes
- **HTMX** for interactivity
- **Accessible** (ARIA labels)

---

### JavaScript Style

- **Modern ES6+**
- **Async/await** for async operations
- **Fetch API** for requests
- **Minimal dependencies**

---

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Make changes
4. Write tests
5. Ensure tests pass
6. Update documentation
7. Submit pull request
8. Address review feedback

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `style`: Code style changes
- `perf`: Performance improvement

**Example:**
```
feat: Add weekly report email automation

- Implemented APScheduler for weekly reports
- Added email templates for reports
- Created user preferences for report frequency

Closes #123
```

---

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Database connection errors:**
```bash
# Check DATABASE_URL in .env
# Verify database is running
# Run migrations: alembic upgrade head
```

**Port already in use:**
```bash
# Change port
uvicorn app.main:app --reload --port 8001
```

**Module not found:**
```bash
# Ensure virtual environment is activated
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Useful Commands

### Database

```bash
# Create migration
alembic revision -m "add_new_table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current version
alembic current

# View migration history
alembic history
```

### Development

```bash
# Run with specific environment
ENV=dev python run_local.py

# Run with debug logging
python run_local.py --debug

# Check code style
flake8 app/

# Format code
black app/
```

### Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_ai_services.py::TestAIService::test_suggest_category

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Run performance tests
pytest -m performance

# Generate coverage report
pytest --cov=app --cov-report=html
```

---

## Project Configuration Files

### requirements.txt
Python dependencies with pinned versions

### alembic.ini
Database migration configuration

### pytest.ini
Test configuration and markers

### .env
Environment variables (not in git, create from .env.example)

### docker-compose.yaml
Docker services configuration

### Procfile
Heroku deployment configuration

---

## Additional Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [HTMX Docs](https://htmx.org/docs/)
- [Chart.js Docs](https://www.chartjs.org/docs/)

### Project Documentation
- `README.md` - Project overview
- `TECHNICAL_ARCHITECTURE.md` - Architecture details
- `API_DOCUMENTATION.md` - API reference
- `USER_GUIDE.md` - User documentation
- `IMPLEMENTATION_ROADMAP.md` - Development roadmap

---

## Getting Help

### Internal Resources
- Check existing documentation
- Review code comments
- Read test files for examples

### External Help
- GitHub Issues
- Stack Overflow
- FastAPI Discord
- Python Discord

---

## Development Best Practices

### 1. Always Use Virtual Environment
Never install packages globally

### 2. Keep Dependencies Updated
```bash
pip list --outdated
pip install --upgrade package-name
```

### 3. Write Tests First
Follow TDD (Test-Driven Development) when possible

### 4. Commit Frequently
Small, focused commits are better than large ones

### 5. Document Your Code
Add docstrings and comments for complex logic

### 6. Review Your Own Code
Before submitting PR, review your changes

### 7. Keep Branches Updated
```bash
git fetch origin
git rebase origin/main
```

---

## Performance Optimization

### Database

- Use indexes on frequently queried fields
- Optimize queries with `explain analyze`
- Use connection pooling
- Implement caching where appropriate

### Application

- Use async/await for I/O operations
- Lazy load heavy resources
- Cache expensive computations
- Optimize ML model loading

### Frontend

- Minimize HTMX target sizes
- Use pagination for large lists
- Optimize chart rendering
- Compress static assets

---

## Security Considerations

### Development

- Never commit `.env` file
- Use strong `SECRET_KEY`
- Don't expose sensitive data in logs
- Test with realistic data, not production data

### Production

- Use environment variables for secrets
- Enable HTTPS
- Set secure cookie flags
- Implement rate limiting
- Regular security audits

---

## Monitoring & Logging

### Application Logs

```python
import logging

logger = logging.getLogger(__name__)
logger.info("User logged in", user_id=user.id)
logger.error("Failed to generate report", error=str(e))
```

### Health Check

**Endpoint:** `GET /healthz`

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-16T10:30:00"
}
```

---

## FAQ for Developers

**Q: How do I add a new model?**
A: Create in `app/models/`, import in `app/main.py`, create migration with Alembic

**Q: How do I add a new API endpoint?**
A: Add to appropriate router in `app/api/v1/`, include router in `app/api/routes.py`

**Q: How do I add a new service?**
A: Create in `app/services/`, follow existing service patterns

**Q: How do I add a new template?**
A: Create in `app/templates/`, extend `base.html`

**Q: How do I debug database queries?**
A: Enable SQLAlchemy echo: `engine = create_engine(url, echo=True)`

---

## Support

**Issues:** https://github.com/TurtleWithGlasses/expense-manager-web-app/issues  
**Discussions:** https://github.com/TurtleWithGlasses/expense-manager-web-app/discussions  
**Email:** dev@budgetpulse.com

---

**Happy coding! 🚀**

*Last updated: January 2025*

