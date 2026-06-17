# 📚 Library Management System

A full-featured **Library Management System** built with Flask and MySQL. Manage books, students, issue/return workflows, fines, reports, and more — all from a clean, responsive web interface.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Screenshots](#-screenshots)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Default Credentials](#-default-credentials)
- [Project Structure](#-project-structure)
- [API Routes](#-api-routes)
- [Database Schema](#-database-schema)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Deployment](#-deployment)
- [Running Tests](#-running-tests)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## ✨ Features

| Category | Highlights |
|---|---|
| **Authentication & Security** | Session-based login, password hashing, CSRF protection, role-based access control |
| **Dashboard & Analytics** | At-a-glance stats — total books, active issues, overdue alerts, recent activity |
| **Book Management** | Full CRUD, search & filter, category tagging, quantity tracking |
| **Student Management** | Full CRUD, profile pages, enrollment-number lookup, department filtering |
| **Issue & Return Management** | One-click issue/return, automatic due-date calculation, overdue detection |
| **Fine Calculation** | Configurable per-day fine for overdue returns, fine history per student |
| **Reports** | Export PDF & Excel reports for books, students, and transactions |
| **QR Code Generation** | Generate QR codes for book identification and quick lookup |
| **Activity Logging** | Track all CRUD operations with timestamps and user attribution |
| **Responsive Design** | Mobile-friendly UI built with Bootstrap 5 |

---

## 🛠 Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core language |
| **Flask 3.0** | Web framework |
| **MySQL 8.0** | Relational database |
| **Flask-Login** | Session & authentication management |
| **Flask-WTF** | Form handling & CSRF protection |
| **Flask-MySQLdb** | MySQL connector for Flask |
| **ReportLab** | PDF report generation |
| **openpyxl** | Excel export |
| **qrcode** | QR code generation |
| **Bootstrap 5** | Frontend UI framework (CDN) |
| **Docker & Docker Compose** | Containerised deployment |
| **Gunicorn** | Production WSGI server |
| **Jenkins** | CI/CD automation |
| **Nginx** | Reverse proxy |

---

## 📸 Screenshots

> Screenshots will be added here once the UI is finalised.

| Page | Description |
|---|---|
| **Login** | Clean login page with validation |
| **Dashboard** | Analytics cards and recent-activity feed |
| **Books** | Searchable, paginated book catalogue |
| **Students** | Student directory with profile links |
| **Issues** | Active issues with status badges |
| **Reports** | PDF / Excel export interface |

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **MySQL 8.0** — [Download](https://dev.mysql.com/downloads/)
- **Docker & Docker Compose** *(optional, for containerised setup)* — [Download](https://docs.docker.com/get-docker/)
- **Git** — [Download](https://git-scm.com/)

> **Note:** Node.js is **not** required. All frontend assets are served via CDN.

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/library-management-system.git
cd library-management-system

# 2. Copy the example env file and edit it
cp .env.example .env
# Edit .env with your preferred settings (DB credentials, secret key, etc.)

# 3. Build and start the containers
docker-compose up -d

# 4. Open in your browser
#    http://localhost
```

### Option 2 — Manual Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/library-management-system.git
cd library-management-system

# 2. Create and activate a virtual environment
python -m venv venv

# On Linux / macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up MySQL
#    Create a database called `library_db` and import the schema:
mysql -u root -p library_db < database/schema.sql

# 5. Initialise the database (seed default admin user, etc.)
python database/init_db.py

# 6. Run the application
python app.py

# 7. Open in your browser
#    http://localhost:5000
```

---

## 🔑 Default Credentials

| Field | Value |
|---|---|
| **Username** | `admin` |
| **Password** | `admin123` |

> ⚠️ **Change the default password immediately** in production environments.

---

## 📁 Project Structure

```
library-management-system/
├── app.py                      # Application entry point
├── config.py                   # Configuration loader
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Multi-container orchestration
├── Jenkinsfile                 # CI/CD pipeline definition
├── .env.example                # Environment variable template
│
├── database/
│   ├── schema.sql              # Database schema (tables, indexes)
│   └── init_db.py              # DB initialisation & seed script
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Login / logout routes
│   ├── dashboard.py            # Dashboard & analytics
│   ├── books.py                # Book CRUD routes
│   ├── students.py             # Student CRUD routes
│   ├── issues.py               # Issue / return routes
│   └── reports.py              # PDF & Excel export routes
│
├── templates/
│   ├── base.html               # Base layout with navbar
│   ├── login.html
│   ├── dashboard.html
│   ├── books/
│   │   ├── list.html
│   │   ├── add.html
│   │   └── edit.html
│   ├── students/
│   │   ├── list.html
│   │   ├── add.html
│   │   ├── edit.html
│   │   └── profile.html
│   └── issues/
│       ├── list.html
│       └── add.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── deployment/
│   ├── deployment-guide.md     # Full deployment instructions
│   └── nginx.conf              # Nginx reverse-proxy config
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # Shared fixtures & helpers
    ├── test_auth.py            # Authentication tests
    ├── test_books.py           # Book management tests
    ├── test_students.py        # Student management tests
    └── test_issues.py          # Issue / return tests
```

---

## 🌐 API Routes

| Method | Route | Description | Auth Required |
|---|---|---|---|
| `GET` | `/login` | Render login page | ❌ |
| `POST` | `/login` | Authenticate user | ❌ |
| `GET` | `/logout` | Log out current user | ✅ |
| `GET` | `/dashboard` | Dashboard with analytics | ✅ |
| `GET` | `/books` | List all books (supports `?search=`) | ✅ |
| `GET` | `/books/add` | Render add-book form | ✅ |
| `POST` | `/books/add` | Create a new book | ✅ |
| `GET` | `/books/edit/<id>` | Render edit-book form | ✅ |
| `POST` | `/books/edit/<id>` | Update an existing book | ✅ |
| `POST` | `/books/delete/<id>` | Delete a book | ✅ |
| `GET` | `/students` | List all students (supports `?search=`) | ✅ |
| `GET` | `/students/add` | Render add-student form | ✅ |
| `POST` | `/students/add` | Create a new student | ✅ |
| `GET` | `/students/<id>` | Student profile page | ✅ |
| `GET` | `/students/edit/<id>` | Render edit-student form | ✅ |
| `POST` | `/students/edit/<id>` | Update student details | ✅ |
| `POST` | `/students/delete/<id>` | Delete a student | ✅ |
| `GET` | `/issues` | List all issues (supports `?status=`) | ✅ |
| `GET` | `/issues/add` | Render issue-book form | ✅ |
| `POST` | `/issues/add` | Issue a book to a student | ✅ |
| `POST` | `/issues/return/<id>` | Return an issued book | ✅ |
| `GET` | `/reports/books` | Export books report (PDF/Excel) | ✅ |
| `GET` | `/reports/students` | Export students report | ✅ |
| `GET` | `/reports/issues` | Export issues report | ✅ |

---

## 🗄 Database Schema

The system uses **four core tables** plus a logging table:

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    books     │       │     issues       │       │   students   │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ book_id (FK)     │──────►│ id (PK)      │
│ title        │       │ student_id (FK)  │       │ name         │
│ author       │       │ issue_date       │       │ email        │
│ isbn         │       │ due_date         │       │ phone        │
│ publisher    │       │ return_date      │       │ department   │
│ quantity     │       │ fine_amount      │       │ enrollment_no│
│ category     │       │ status           │       │ semester     │
│ created_at   │       │ created_at       │       │ created_at   │
└──────────────┘       └──────────────────┘       └──────────────┘

┌──────────────┐       ┌──────────────────┐
│    users     │       │  activity_log    │
├──────────────┤       ├──────────────────┤
│ id (PK)      │       │ id (PK)          │
│ username     │       │ user_id (FK)     │
│ password     │       │ action           │
│ role         │       │ description      │
│ created_at   │       │ timestamp        │
└──────────────┘       └──────────────────┘
```

---

## ⚙️ CI/CD Pipeline

The project uses a **Jenkins** pipeline triggered by a **GitHub webhook**:

```
┌────────┐     webhook     ┌──────────┐     build     ┌────────┐     deploy     ┌────────────┐
│ GitHub │────────────────►│ Jenkins  │──────────────►│ Docker │───────────────►│ Production │
│  Push  │                 │ Pipeline │               │ Build  │                │  Server    │
└────────┘                 └──────────┘               └────────┘                └────────────┘
```

### Pipeline Stages

1. **Checkout** — Pull latest code from the repository
2. **Install Dependencies** — `pip install -r requirements.txt`
3. **Lint** — Run `flake8` for code-quality checks
4. **Test** — Run `pytest tests/ -v --tb=short`
5. **Build** — Build the Docker image
6. **Push** — Push the image to a container registry
7. **Deploy** — Deploy updated containers via `docker-compose`

---

## 🚢 Deployment

For full deployment instructions (server setup, Nginx config, SSL, etc.) see:

📄 [`deployment/deployment-guide.md`](deployment/deployment-guide.md)

**Quick production checklist:**

- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Use a strong `SECRET_KEY`
- [ ] Change default admin credentials
- [ ] Configure MySQL with a dedicated user (not `root`)
- [ ] Enable HTTPS via Let's Encrypt / Certbot
- [ ] Set up log rotation
- [ ] Configure automated database backups

---

## 🧪 Running Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_auth.py -v

# Run tests with coverage report
pytest tests/ --cov=. --cov-report=html

# Open the HTML coverage report
open htmlcov/index.html        # macOS
xdg-open htmlcov/index.html    # Linux
start htmlcov/index.html       # Windows
```

### Test Structure

| File | Scope | Test Count |
|---|---|---|
| `tests/test_auth.py` | Login, logout, session, access control | 14 |
| `tests/test_books.py` | Book CRUD, search, validation | 16 |
| `tests/test_students.py` | Student CRUD, profiles, search | 18 |
| `tests/test_issues.py` | Issue, return, fines, filtering | 18 |

---

## 🔧 Configuration

All configuration is managed via environment variables. Copy `.env.example` to `.env` and customise:

| Variable | Description | Default |
|---|---|---|
| `FLASK_ENV` | Environment mode (`development` / `production`) | `development` |
| `SECRET_KEY` | Flask secret key for sessions & CSRF | `change-me` |
| `MYSQL_HOST` | MySQL server hostname | `localhost` |
| `MYSQL_PORT` | MySQL server port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | *(empty)* |
| `MYSQL_DB` | Database name | `library_db` |
| `FINE_PER_DAY` | Fine charged per overdue day (₹) | `5` |
| `MAX_ISSUE_DAYS` | Default loan period in days | `14` |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes
   ```bash
   git commit -m "feat: add amazing feature"
   ```
4. **Push** to the branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — adding / updating tests
- `chore:` — maintenance tasks

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) — lightweight Python web framework
- [Bootstrap 5](https://getbootstrap.com/) — responsive CSS framework
- [ReportLab](https://www.reportlab.com/) — PDF generation library
- [Font Awesome](https://fontawesome.com/) — icon toolkit
- [Docker](https://www.docker.com/) — containerisation platform
- [Jenkins](https://www.jenkins.io/) — automation server

---

<p align="center">
  Made with ❤️ for learning and open-source
</p>
