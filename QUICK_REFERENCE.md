# Budget Pulse - Quick Reference

Quick reference guide for common tasks and commands.

---

## 🚀 Quick Start

```bash
# Setup
git clone https://github.com/TurtleWithGlasses/expense-manager-web-app.git
cd expense-manager-web-app
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run
python run_local.py
# Visit: http://localhost:8000
```

---

## 🧪 Testing Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ai_services.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only AI tests
pytest -m ai

# Run only performance tests
pytest -m performance

# Run only integration tests
pytest -m integration

# Verbose output
pytest -v

# Show print statements
pytest -s
```

---

## 💾 Database Commands

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision -m "description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (⚠️ deletes all data!)
python reset_db.py
```

---

## 🔧 Development Commands

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run on different port
uvicorn app.main:app --reload --port 8001

# Run with Gunicorn (production-like)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Check code style
flake8 app/

# Format code
black app/
```

---

## 📁 Project Structure Quick Map

```
app/
├── api/v1/          # API endpoints
├── services/        # Business logic
├── models/          # Database models
├── ai/              # ML components
├── templates/       # HTML templates
└── core/            # Configuration

tests/
├── integration/     # Integration tests
├── performance/     # Performance tests
└── test_*.py        # Unit tests
```

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | Application entry point |
| `app/deps.py` | FastAPI dependencies |
| `app/core/config.py` | Configuration |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables |
| `alembic.ini` | Migration config |
| `pytest.ini` | Test configuration |

---

## 🌐 API Endpoints Quick Reference

### Authentication
- `POST /auth/register` - Register
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout

### Entries
- `GET /entries/` - List entries
- `POST /entries/create` - Create entry
- `POST /entries/delete/{id}` - Delete entry

### AI
- `POST /ai/suggest-category` - Get suggestion
- `POST /ai/model/train` - Train model
- `GET /ai/model/status` - Model status

### Reports
- `GET /reports/weekly` - Weekly report
- `GET /reports/monthly` - Monthly report
- `POST /reports/weekly/email` - Email report

### Currency
- `GET /currency/settings` - Currency page
- `POST /currency/update` - Update currency

---

## 🎨 Common HTML Patterns

### HTMX Form
```html
<form hx-post="/entries/create" 
      hx-target="#entries-list" 
      hx-swap="outerHTML">
  <!-- form fields -->
</form>
```

### HTMX Button
```html
<button hx-get="/dashboard/summary" 
        hx-target="#summary-panel">
  Refresh
</button>
```

---

## 🐍 Common Python Patterns

### Create Service
```python
from sqlalchemy.orm import Session

def create_item(db: Session, user_id: int, data: dict):
    item = Item(user_id=user_id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
```

### API Endpoint
```python
@router.get("/endpoint")
async def endpoint(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    # Logic here
    return render(request, "template.html", context)
```

---

## 🔍 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database
```python
# In Python shell
from app.db.session import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()
print(users)
```

### Test Email
```python
# Create test script
from app.services.email import email_service
await email_service.send_email(
    "test@example.com",
    "Test Subject",
    "<h1>Test</h1>",
    "Test text"
)
```

---

## 🔐 Environment Variables

```bash
# Required
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key
ENV=dev

# Email (optional but recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Alternative email
RESEND_API_KEY=your-resend-key
```

---

## 🎯 Common Tasks

### Add New Model
1. Create in `app/models/`
2. Import in `app/main.py`
3. Create migration: `alembic revision -m "add_model"`
4. Edit migration file
5. Apply: `alembic upgrade head`

### Add New API Endpoint
1. Add to router in `app/api/v1/`
2. Include router in `app/api/routes.py`
3. Create service in `app/services/` if needed
4. Create template in `app/templates/` if needed
5. Write tests

### Add New Service
1. Create in `app/services/`
2. Follow existing patterns
3. Use dependency injection
4. Write unit tests
5. Document with docstrings

---

## 🆘 Quick Troubleshooting

### Server Won't Start
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for port conflicts
netstat -ano | findstr :8000
```

### Database Errors
```bash
# Reset database
python reset_db.py

# Reapply migrations
alembic upgrade head

# Check DATABASE_URL
echo $env:DATABASE_URL  # PowerShell
```

### Import Errors
```bash
# Activate virtual environment
.venv\Scripts\activate

# Reinstall package
pip install -e .

# Check PYTHONPATH
$env:PYTHONPATH = "."
```

---

## 📞 Support

- **GitHub Issues:** Report bugs
- **Documentation:** See detailed guides
- **Email:** support@budgetpulse.com

---

**Quick reference for developers - keep this handy!** 🎯

