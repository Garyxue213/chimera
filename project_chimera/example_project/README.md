# TaskFlow - Team Todo Application

A collaborative task management web application built with Flask and SQLite.

## Project Overview

TaskFlow is a simple but functional todo application that teams can use to manage their tasks. The project includes:

- **Backend API** (Flask + SQLite)
- **Frontend UI** (HTML/CSS/JavaScript)
- **User Authentication** (Login/Registration)
- **Task Management** (CRUD operations)
- **Team Collaboration** (Shared tasks, assignments)

## Current Status

🟡 **In Development** - Basic functionality implemented, needs additional features and improvements.

## Architecture

```
example_project/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication routes
│   ├── tasks.py            # Task management routes
│   └── database.db         # SQLite database
├── frontend/
│   ├── index.html          # Main page
│   ├── login.html          # Login page
│   ├── styles.css          # Styling
│   └── app.js              # Frontend JavaScript
├── tests/
│   ├── test_auth.py        # Authentication tests
│   └── test_tasks.py       # Task management tests
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup Instructions

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize database: `python backend/app.py init-db`
3. Run server: `python backend/app.py`
4. Open browser: `http://localhost:5000`

## Current Tasks & Issues

### High Priority 🔴
- [ ] Fix user authentication bug (users can't log out properly)
- [ ] Add input validation for task creation
- [ ] Implement task assignment notifications

### Medium Priority 🟡
- [ ] Add task due dates and reminders
- [ ] Create team dashboard view
- [ ] Implement task priority levels
- [ ] Add search/filter functionality

### Low Priority 🟢
- [ ] Dark mode UI theme
- [ ] Export tasks to CSV
- [ ] Mobile responsive design
- [ ] Add task categories/tags

### Known Bugs 🐛
- Login session sometimes expires unexpectedly
- Task deletion doesn't update UI immediately
- Database connection pool occasionally exhausted

## Development Guidelines

- All code changes require review
- Write tests for new functionality
- Follow PEP 8 style guidelines
- Update documentation for API changes

## Team Members

- **Project Lead**: @pm_user
- **Backend Developer**: @backend_dev
- **Frontend Developer**: @frontend_dev
- **QA Tester**: @qa_tester
