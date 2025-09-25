# Technical Architecture & Patterns

## Technology Stack

### Backend Technologies
- **Python 3.12+**: Core programming language
- **FastAPI 0.115.0**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.0.35**: Python SQL toolkit and Object-Relational Mapping (ORM)
- **Alembic 1.13.2**: Database migration tool for SQLAlchemy
- **Pydantic 2.8.2**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI applications
- **Gunicorn 21.2.0**: WSGI HTTP Server for production deployment

### Database Technologies
- **PostgreSQL**: Primary production database
- **SQLite**: Development and fallback database
- **psycopg2-binary 2.9.9**: PostgreSQL adapter for Python
- **Database Migrations**: Alembic for schema versioning

### Frontend Technologies
- **HTML5**: Semantic markup structure
- **Tailwind CSS**: Utility-first CSS framework
- **HTMX**: Dynamic HTML with minimal JavaScript
- **Chart.js**: Interactive data visualization
- **Jinja2 3.1.4**: Template engine for server-side rendering

### Security & Authentication
- **Passlib 1.7.4**: Password hashing library
- **bcrypt 4.0.1**: Password hashing algorithm
- **itsdangerous 2.2.0**: Secure token generation and validation
- **Session Management**: Custom session handling with secure cookies

### External Services
- **Email Services**: SMTP integration with multiple providers
- **Exchange Rate API**: Real-time currency conversion
- **Resend API**: Alternative email service provider

## Architectural Patterns

### 1. Layered Architecture (N-Tier)
```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│  (Templates, HTMX, Static Files)   │
├─────────────────────────────────────┤
│            API Layer               │
│     (FastAPI Routes, Endpoints)    │
├─────────────────────────────────────┤
│          Business Logic Layer      │
│      (Services, Business Rules)    │
├─────────────────────────────────────┤
│          Data Access Layer         │
│        (SQLAlchemy ORM, Models)    │
├─────────────────────────────────────┤
│           Database Layer           │
│      (PostgreSQL/SQLite)           │
└─────────────────────────────────────┘
```

### 2. Model-View-Controller (MVC) Pattern
- **Models**: SQLAlchemy ORM models representing database entities
- **Views**: Jinja2 templates for rendering HTML responses
- **Controllers**: FastAPI route handlers managing request/response flow

### 3. Repository Pattern
- **Service Layer**: Business logic abstraction
- **Data Access**: Centralized database operations
- **Dependency Injection**: FastAPI's dependency system for loose coupling

### 4. Dependency Injection Pattern
```python
# Example from the codebase
@router.get("/entries/")
async def page(
    request: Request,
    user=Depends(current_user),  # Dependency injection
    db: Session = Depends(get_db)  # Database dependency
) -> HTMLResponse:
```

## Database Design Patterns

### 1. Entity-Relationship Model
```
Users (1) ──── (N) Categories
  │
  └── (N) Entries ──── (1) Categories
  │
  └── (1) UserPreferences
```

### 2. Database Schema Design
- **Normalization**: Third normal form (3NF) compliance
- **Foreign Key Constraints**: Referential integrity enforcement
- **Cascade Operations**: Proper data cleanup on deletion
- **Indexing Strategy**: Optimized query performance

### 3. Migration Management
- **Version Control**: Alembic migration versioning
- **Schema Evolution**: Safe database schema updates
- **Rollback Capability**: Ability to revert changes
- **Data Integrity**: Migration validation and testing

## API Design Patterns

### 1. RESTful API Design
```
GET    /entries/          # List entries
POST   /entries/create    # Create entry
GET    /entries/{id}      # Get specific entry
POST   /entries/update/{id} # Update entry
POST   /entries/delete/{id} # Delete entry
```

### 2. HTMX Integration Pattern
- **Server-Side Rendering**: HTML fragments returned for dynamic updates
- **Progressive Enhancement**: Works without JavaScript
- **Partial Page Updates**: Efficient DOM manipulation
- **Form Handling**: Seamless form submission and validation

### 3. Error Handling Pattern
```python
try:
    # Business logic
    result = process_data()
    return success_response(result)
except ValueError as e:
    return error_response(str(e))
except Exception as e:
    return generic_error_response()
```

## Security Patterns

### 1. Authentication & Authorization
- **Session-Based Authentication**: Secure session management
- **Password Hashing**: bcrypt with salt rounds
- **Token-Based Verification**: Secure email verification tokens
- **Password Reset Flow**: Time-limited reset tokens

### 2. Data Validation
- **Input Sanitization**: Pydantic model validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Template escaping
- **CSRF Protection**: Form token validation

### 3. Security Headers
- **Secure Cookies**: HttpOnly, Secure flags
- **Session Timeout**: Configurable session expiration
- **Rate Limiting**: Protection against brute force attacks

## Design Patterns Implementation

### 1. Factory Pattern
```python
# Currency service factory
class CurrencyService:
    def __init__(self):
        self.base_currency = "USD"
        self._exchange_rates = None
```

### 2. Singleton Pattern
```python
# Configuration singleton
settings = Settings()
```

### 3. Strategy Pattern
```python
# Different email sending strategies
class EmailService:
    async def send_email(self, strategy="smtp"):
        if strategy == "smtp":
            return await self._send_smtp()
        elif strategy == "resend":
            return await self._send_resend()
```

### 4. Observer Pattern
```python
# HTMX event handling
@router.post("/entries/create")
async def create_entry(request: Request, ...):
    # Process creation
    # Return updated HTML fragment
    return render(request, "entries/_list.html", {"entries": entries})
```

## Performance Patterns

### 1. Database Optimization
- **Query Optimization**: Efficient SQL queries
- **Connection Pooling**: Database connection management
- **Lazy Loading**: On-demand data loading
- **Caching Strategy**: Exchange rate caching

### 2. Frontend Performance
- **HTMX Efficiency**: Minimal JavaScript overhead
- **Template Caching**: Jinja2 template optimization
- **Static File Serving**: Optimized asset delivery
- **Progressive Loading**: Incremental content loading

### 3. Scalability Patterns
- **Horizontal Scaling**: Stateless application design
- **Database Sharding**: User-based data partitioning
- **Microservices Ready**: Modular architecture
- **API Versioning**: Backward compatibility support

## Deployment Patterns

### 1. Containerization
- **Docker Support**: Containerized deployment
- **Environment Configuration**: 12-factor app principles
- **Health Checks**: Application monitoring endpoints

### 2. Production Deployment
- **WSGI Server**: Gunicorn for production
- **Reverse Proxy**: Nginx configuration ready
- **Database Migration**: Automated schema updates
- **Environment Variables**: Configuration management

### 3. Monitoring & Logging
- **Health Endpoints**: `/healthz` for monitoring
- **Error Logging**: Comprehensive error tracking
- **Performance Metrics**: Database and API monitoring
- **Audit Trail**: User action logging

## Code Organization Patterns

### 1. Modular Structure
```
app/
├── api/           # API routes and endpoints
├── core/          # Core configuration and utilities
├── db/            # Database configuration and models
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic data models
├── services/      # Business logic layer
└── templates/     # Jinja2 HTML templates
```

### 2. Separation of Concerns
- **API Layer**: Request/response handling
- **Service Layer**: Business logic implementation
- **Data Layer**: Database operations
- **Template Layer**: Presentation logic

### 3. Configuration Management
- **Environment-Based**: Different configs for dev/prod
- **Type Safety**: Pydantic settings validation
- **Secret Management**: Secure credential handling
- **Feature Flags**: Configurable feature toggles

## Testing Patterns

### 1. Test Structure
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: Model and migration testing
- **End-to-End Tests**: Full user workflow testing

### 2. Test Data Management
- **Fixtures**: Reusable test data
- **Database Seeding**: Test data population
- **Mock Services**: External service mocking
- **Cleanup**: Test data isolation

## Future Architecture Considerations

### 1. Microservices Migration
- **Service Decomposition**: Break into smaller services
- **API Gateway**: Centralized request routing
- **Event-Driven Architecture**: Asynchronous communication
- **Service Discovery**: Dynamic service registration

### 2. AI Integration Architecture
- **ML Service Layer**: Dedicated AI/ML services
- **Model Serving**: AI model deployment
- **Data Pipeline**: Feature engineering and training
- **API Integration**: External AI service integration

### 3. Scalability Enhancements
- **Caching Layer**: Redis integration
- **Message Queues**: Asynchronous processing
- **CDN Integration**: Global content delivery
- **Load Balancing**: Traffic distribution

