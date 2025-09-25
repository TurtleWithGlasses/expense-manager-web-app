# Budget Pulse - Expense Manager Web App

## What This App Does

Budget Pulse is a comprehensive personal finance management web application designed to help users track, manage, and analyze their income and expenses. The app provides a modern, intuitive interface for financial data entry, categorization, and visualization, making it easy for users to understand their spending patterns and maintain healthy financial habits.

### Core Purpose
- **Financial Tracking**: Record income and expense transactions with detailed categorization
- **Budget Management**: Monitor spending patterns and financial health through visual analytics
- **Multi-Currency Support**: Handle transactions in various currencies with real-time exchange rate conversion
- **Data Visualization**: Provide interactive charts and graphs for financial insights
- **User-Centric Design**: Personalized experience with customizable preferences and settings

## Key Functions

### 1. Transaction Management
- **Income Tracking**: Record salary, freelance income, investments, and other revenue sources
- **Expense Recording**: Log purchases, bills, subscriptions, and other expenditures
- **Categorization**: Organize transactions into custom categories for better analysis
- **Date Management**: Track transactions by specific dates with historical data
- **Notes & Descriptions**: Add contextual information to each transaction

### 2. Category Management
- **Custom Categories**: Create personalized spending categories (e.g., "Groceries", "Entertainment", "Transportation")
- **Category Editing**: Modify category names and manage existing categories
- **Category Deletion**: Remove unused categories with proper data handling
- **Visual Organization**: Clean, intuitive category management interface

### 3. Financial Analytics
- **Summary Dashboards**: Real-time overview of total income, expenses, and net worth
- **Interactive Charts**: Multiple visualization types including pie charts, bar charts, and daily trend graphs
- **Date Range Filtering**: Analyze financial data for specific time periods
- **Category Breakdown**: Understand spending patterns by category
- **Trend Analysis**: Track financial changes over time

### 4. Multi-Currency Support
- **Currency Selection**: Choose from 13+ supported currencies (USD, EUR, GBP, JPY, etc.)
- **Real-Time Conversion**: Automatic currency conversion using live exchange rates
- **Historical Data Preservation**: Maintain original currency information for accurate reporting
- **Exchange Rate Display**: View current exchange rates and conversion information

### 5. User Account Management
- **Secure Registration**: Email-based account creation with verification
- **Password Security**: Bcrypt hashing with secure password reset functionality
- **Email Verification**: Account activation through email confirmation
- **Session Management**: Secure user sessions with configurable timeouts
- **Password Recovery**: Self-service password reset via email

## Technical Features

### Backend Architecture
- **FastAPI Framework**: Modern, high-performance Python web framework
- **SQLAlchemy ORM**: Robust database abstraction with relationship management
- **Alembic Migrations**: Database schema versioning and migration management
- **Pydantic Validation**: Type-safe data validation and serialization
- **Async/Await Support**: Non-blocking I/O operations for better performance

### Database Design
- **PostgreSQL/SQLite Support**: Flexible database backend with production-ready options
- **Normalized Schema**: Well-structured relational database design
- **Foreign Key Relationships**: Proper data integrity with cascading operations
- **Indexed Queries**: Optimized database performance with strategic indexing
- **Migration System**: Version-controlled database schema evolution

### Frontend Technology
- **HTMX Integration**: Dynamic, interactive web pages without complex JavaScript frameworks
- **Jinja2 Templating**: Server-side rendering with template inheritance
- **Tailwind CSS**: Utility-first CSS framework for responsive, modern design
- **Chart.js Integration**: Interactive data visualization and analytics
- **Progressive Enhancement**: Works without JavaScript, enhanced with it

### Security Features
- **Password Hashing**: Bcrypt encryption for secure password storage
- **Session Security**: Secure session management with configurable timeouts
- **CSRF Protection**: Cross-site request forgery prevention
- **Input Validation**: Comprehensive data validation and sanitization
- **SQL Injection Prevention**: Parameterized queries and ORM protection

### Email System
- **SMTP Integration**: Reliable email delivery through multiple providers
- **Email Templates**: Professional HTML email templates for notifications
- **Verification System**: Account activation and password reset workflows
- **Fallback Mechanisms**: Multiple email service providers for reliability

## What It Provides to Users

### 1. Financial Clarity
- **Complete Financial Picture**: Comprehensive view of income and expenses
- **Spending Insights**: Understanding where money goes through categorization
- **Trend Analysis**: Historical data to identify spending patterns
- **Budget Awareness**: Real-time financial health monitoring

### 2. User Experience
- **Intuitive Interface**: Clean, modern design that's easy to navigate
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-Time Updates**: Instant data refresh without page reloads
- **Customizable Views**: Personalized dashboard with color preferences

### 3. Data Management
- **Secure Storage**: Encrypted, reliable data storage with backup capabilities
- **Data Export**: Ability to export financial data for external analysis
- **Historical Access**: Complete transaction history with search capabilities
- **Multi-Device Sync**: Access data from any device with internet connection

### 4. Analytical Tools
- **Visual Analytics**: Charts and graphs for easy data interpretation
- **Custom Date Ranges**: Flexible time period analysis
- **Category Analysis**: Deep dive into spending by category
- **Financial Health Metrics**: Key performance indicators for financial wellness

## User Types and Capabilities

### Primary Users: Individual Consumers
- **Personal Finance Management**: Track personal income and expenses
- **Budget Planning**: Plan and monitor monthly/yearly budgets
- **Financial Goal Setting**: Set and track financial objectives
- **Expense Categorization**: Organize spending for better financial awareness

### User Capabilities
1. **Account Management**
   - Create and manage personal accounts
   - Update profile information and preferences
   - Manage security settings and password changes
   - Email verification and account recovery

2. **Transaction Operations**
   - Add new income and expense entries
   - Edit existing transactions
   - Delete unwanted entries
   - Categorize transactions appropriately

3. **Data Analysis**
   - View financial summaries and totals
   - Generate custom reports by date range
   - Analyze spending patterns by category
   - Export data for external analysis

4. **System Configuration**
   - Set preferred currency and exchange rates
   - Customize dashboard appearance
   - Configure notification preferences
   - Manage data retention settings

## Current Features

### Core Functionality
- ✅ User registration and authentication
- ✅ Income and expense tracking
- ✅ Category management
- ✅ Multi-currency support with real-time conversion
- ✅ Interactive dashboard with financial summaries
- ✅ Data visualization (pie charts, bar charts, daily trends)
- ✅ Date range filtering and analysis
- ✅ Responsive web design
- ✅ Email verification and password recovery
- ✅ Real-time data updates with HTMX

### User Interface Features
- ✅ Modern, clean dashboard design
- ✅ Color-customizable income/expense displays
- ✅ Intuitive navigation and user flows
- ✅ Mobile-responsive layout
- ✅ Interactive charts and graphs
- ✅ Inline editing capabilities
- ✅ Real-time form validation

### Technical Features
- ✅ RESTful API architecture
- ✅ Database migrations and versioning
- ✅ Secure session management
- ✅ Email service integration
- ✅ Exchange rate API integration
- ✅ Production deployment ready
- ✅ Health check endpoints

