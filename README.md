# OSS Health Monitor

A FastAPI service for scanning GitHub repositories for security vulnerabilities and tracking dependency health metrics over time.

## Overview

This project provides a REST API for scanning GitHub repositories to identify security vulnerabilities and track dependency health metrics. It integrates with Google OSV Scanner and GitHub Security Advisory Database to provide comprehensive vulnerability detection and generates time-series health metrics suitable for tracking project maintenance velocity and sustainability.

## Features

- **Repository Vulnerability Scanning**: Scan GitHub repositories using Google OSV Scanner and GitHub Security Advisory Database
- **Health Metrics**: Track dependency statistics, vulnerability counts by severity, and maintenance indicators
- **Time-Series Analysis**: Store scan history to enable trend analysis and project health monitoring
- **API Key Authentication**: Secure server-to-server API access
- **Result Caching**: 12-hour cache to avoid redundant scans of the same commit
- **Multi-Scanner Support**: Combine results from multiple scanners with automatic deduplication
- FastAPI web server with automatic OpenAPI documentation
- PostgreSQL database with SQLAlchemy ORM
- Docker and Docker Compose support
- Comprehensive test suite with pytest
- GitHub Actions CI/CD workflows

## Prerequisites

- Python 3.10+
- PostgreSQL 12+ (or use Docker Compose)
- Git
- [OSV Scanner](https://github.com/google/osv-scanner) (optional, for vulnerability scanning)
- GitHub Personal Access Token (for API access)
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

4. Install OSV Scanner (optional, but required for vulnerability scanning):
```bash
# On macOS:
brew install osv-scanner

# On Linux:
curl -sSfL https://github.com/google/osv-scanner/releases/latest/download/osv-scanner_linux_amd64 -o /usr/local/bin/osv-scanner
chmod +x /usr/local/bin/osv-scanner
```

5. Create a `.env` file from the example:
```bash
cp .env.example .env
```

6. Update the `.env` file with your configuration:
   - Set `GITHUB_TOKEN` with a GitHub personal access token
   - Update `DATABASE_URL` if needed
   - Set `OSV_SCANNER_PATH` if OSV Scanner is not in your PATH

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

#### Health Endpoints
- `GET /health` - Basic health check (no authentication required)

#### Scan Endpoints
- `POST /v1/scan/repository` - Scan a GitHub repository for vulnerabilities (requires API key authentication)

### Authentication

All scan endpoints require API key authentication. Include your API key in the `Authorization` header:

```bash
Authorization: Bearer <your-api-key>
```

#### Creating API Keys

Use the provided script to create and manage API keys:

```bash
# Create a new API key
python scripts/manage_api_keys.py create "My Service Name"

# List all API keys
python scripts/manage_api_keys.py list

# Disable an API key
python scripts/manage_api_keys.py disable <key_id>

# Enable an API key
python scripts/manage_api_keys.py enable <key_id>
```

### Example: Scanning a Repository

```bash
curl -X POST http://localhost:8000/v1/scan/repository \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": {
      "owner": "psf",
      "name": "requests"
    },
    "scan_config": {
      "scanner": "osv",
      "scan_timeout_seconds": 60
    }
  }'
```

Or use the provided example script:

```bash
export OSS_HEALTH_API_KEY='your-api-key-here'
python scripts/example_scan.py
```

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
├── alembic/
│   ├── versions/           # Database migration scripts
│   ├── env.py              # Alembic environment configuration
│   └── script.py.mako      # Migration script template
├── app/
│   ├── clients/            # External API clients
│   │   └── github.py       # GitHub API client
│   ├── integrations/       # Vulnerability scanner integrations
│   │   ├── base.py         # Abstract scanner interface
│   │   ├── osv_scanner.py  # Google OSV Scanner integration
│   │   └── github_advisory.py # GitHub Advisory API
│   ├── middleware/         # Authentication middleware
│   │   └── auth.py         # API key authentication
│   ├── models/             # Database ORM models
│   │   ├── auth.py         # APIKey model
│   │   ├── repository.py   # RepositoryConfig model
│   │   └── scan.py         # RepositoryScan, ScanVulnerability, ScanMetrics
│   ├── routes/             # API endpoints
│   │   ├── health.py       # Health check endpoints
│   │   └── scan.py         # Repository scan endpoints
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic
│   │   ├── cache.py        # Scan result caching
│   │   ├── metrics_calculator.py # Health metrics computation
│   │   └── scanner_orchestrator.py # Multi-scanner coordination
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection and session
│   └── main.py             # FastAPI application entry point
├── scripts/
│   ├── manage_api_keys.py  # API key management CLI
│   └── example_scan.py     # Example API usage script
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
| `GITHUB_TOKEN` | GitHub personal access token | _(required for API access)_ |
| `OSV_SCANNER_PATH` | Path to osv-scanner binary | `osv-scanner` |
| `SCAN_CACHE_TTL_HOURS` | Cache time-to-live in hours | `12` |
| `SCAN_CACHE_MAX_SIZE` | Maximum cached scan results | `1000` |

## Architecture

### Components

- **Routes** (`app/routes/`): API endpoint handlers
- **Models** (`app/models/`): Database ORM models for scans, vulnerabilities, metrics, and API keys
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation
- **Services** (`app/services/`): Business logic layer
  - `scanner_orchestrator.py`: Coordinates multiple vulnerability scanners in parallel
  - `metrics_calculator.py`: Computes health metrics from scan results
  - `cache.py`: In-memory caching for scan results (12-hour TTL)
- **Integrations** (`app/integrations/`): External scanner integrations
  - `osv_scanner.py`: Google OSV Scanner integration
  - `github_advisory.py`: GitHub Security Advisory API client
- **Clients** (`app/clients/`): External API clients
  - `github.py`: GitHub API client for repository operations
- **Middleware** (`app/middleware/`): Authentication and request processing

### Data Flow

1. API request received with repository information
2. Check cache for recent scan of same commit SHA
3. If not cached, clone repository from GitHub
4. Run configured scanners in parallel (OSV Scanner, GitHub Advisory)
5. Normalize and deduplicate vulnerability results
6. Calculate health metrics (dependency stats, severity counts, temporal metrics)
7. Store results in database (scan record, vulnerabilities, metrics)
8. Cache response for 12 hours
9. Return structured JSON response

### Database Schema

- `repository_scans`: Scan execution records with status and metadata
- `scan_vulnerabilities`: Individual vulnerabilities found in scans
- `scan_metrics`: Aggregated health metrics for time-series analysis
- `repository_configs`: Configuration for scheduled repository scans
- `api_keys`: API authentication keys with scoping and rate limits

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
