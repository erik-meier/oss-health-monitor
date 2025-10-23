# OSS Health Monitor

Monitor open-source (GitHub) repos for project health.

## Overview

This project provides a REST API built with FastAPI and PostgreSQL to monitor and track the health of open-source repositories.

## Features

- FastAPI web server with automatic OpenAPI documentation
- PostgreSQL database with SQLAlchemy ORM
- Health check endpoints
- Docker and Docker Compose support
- Comprehensive test suite with pytest
- GitHub Actions CI/CD workflows
- Code formatting and linting (Black, isort, flake8)

## Prerequisites

- Python 3.9+
- PostgreSQL 12+ (or use Docker Compose)
- Docker and Docker Compose (optional, for containerized deployment)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/erik-meier/oss-health-monitor.git
cd oss-health-monitor
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Update the `.env` file with your database credentials if needed.

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/erik-meier/oss-health-monitor.git
cd oss-health-monitor
```

2. Start the services:
```bash
docker-compose up -d
```

This will start both the PostgreSQL database and the FastAPI application.

## Running the Application

### Local Development

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided run script:
```bash
python run.py
```

### Using Docker Compose

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`.

## Database Migrations

This project uses Alembic for database schema migrations.

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of migration"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migrations

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Available Endpoints

- `GET /health` - Basic health check
- `GET /health/db` - Database connectivity health check

## Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

View the coverage report by opening `htmlcov/index.html` in your browser.

## Code Quality

### Format code
```bash
black app tests
isort app tests
```

### Lint code
```bash
flake8 app tests
```

### Type checking
```bash
mypy app
```

## Project Structure

```
oss-health-monitor/
├── .github/
│   └── workflows/          # GitHub Actions workflows
│       ├── ci.yml          # CI pipeline (lint, test)
│       └── docker.yml      # Docker build workflow
├── alembic/
│   ├── versions/           # Database migration scripts
│   ├── env.py              # Alembic environment configuration
│   └── script.py.mako      # Migration script template
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection and session
│   └── routes/
│       ├── __init__.py
│       └── health.py       # Health check endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_config.py      # Configuration tests
│   └── test_health.py      # Health endpoint tests
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
├── alembic.ini             # Alembic configuration
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker image definition
├── pyproject.toml          # Project metadata and tool configs
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── run.py                  # Application run script
└── README.md               # This file
```

## Environment Variables

The following environment variables can be configured in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `OSS Health Monitor` |
| `APP_VERSION` | Application version | `0.1.0` |
| `DEBUG` | Debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/oss_health_monitor` |
| `DATABASE_ECHO` | Echo SQL queries | `false` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000,http://localhost:8000` |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Contact

Project Link: https://github.com/erik-meier/oss-health-monitor
