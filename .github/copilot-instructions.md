# GitHub Copilot Instructions for OSS Health Monitor

## Project Overview

This is a FastAPI-based service for scanning GitHub repositories for security vulnerabilities and tracking dependency health metrics over time. The service integrates with Google OSV Scanner and GitHub Security Advisory Database to detect vulnerabilities and generates time-series health metrics.

## Architecture

### Tech Stack
- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: API key-based (Bearer token)
- **External Tools**: Google OSV Scanner, GitHub API
- **Caching**: In-memory TTL cache (cachetools)
- **Async**: httpx for async HTTP requests, asyncio for concurrent operations

### Project Structure

```
app/
├── clients/           # External API clients (GitHub)
├── integrations/      # Vulnerability scanner integrations (OSV, GitHub Advisory)
├── middleware/        # Authentication middleware (API key validation)
├── models/           # SQLAlchemy ORM models (scans, vulnerabilities, metrics)
├── routes/           # FastAPI route handlers (health, scan endpoints)
├── schemas/          # Pydantic request/response models
├── services/         # Business logic (orchestrator, metrics, cache)
├── config.py         # Application configuration
├── database.py       # Database session management
└── main.py          # FastAPI app initialization

scripts/
├── manage_api_keys.py  # CLI for API key management
└── example_scan.py     # Example API usage
```

### Key Components

1. **Scanner Orchestrator** (`app/services/scanner_orchestrator.py`): Coordinates multiple vulnerability scanners, runs them in parallel, deduplicates results
2. **Metrics Calculator** (`app/services/metrics_calculator.py`): Computes health metrics from scan results
3. **Scan Cache** (`app/services/cache.py`): In-memory cache with 12-hour TTL to avoid redundant scans
4. **GitHub Client** (`app/clients/github.py`): Clones repos, fetches metadata, resolves commit SHAs
5. **OSV Scanner** (`app/integrations/osv_scanner.py`): Executes osv-scanner binary, parses JSON output
6. **Auth Middleware** (`app/middleware/auth.py`): Validates API keys, updates last_used_at

## Database Models

### Core Models
- **RepositoryScan**: Main scan record (id, repo info, status, timestamps, config)
- **ScanVulnerability**: Individual vulnerabilities (package, version, vuln_id, severity, CVSS)
- **ScanMetrics**: Aggregated metrics (dependency counts, severity counts, temporal metrics)
- **RepositoryConfig**: Scheduled scan configuration
- **APIKey**: Authentication keys (hashed, with expiration and scopes)

### Relationships
- RepositoryScan → many ScanVulnerability
- RepositoryScan → one ScanMetrics

## Common Development Tasks

### Adding a New Route

1. Create route handler in `app/routes/`
2. Define Pydantic schemas in `app/schemas/`
3. Register router in `app/main.py`
4. Add authentication with `Depends(get_current_api_key)` if needed

Example:
```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_api_key

router = APIRouter(prefix="/v1/example")

@router.get("/")
async def example_endpoint(api_key = Depends(get_current_api_key)):
    return {"status": "ok"}
```

### Adding a New Database Model

1. Create model class in `app/models/` inheriting from `Base`
2. Import model in `app/models/__init__.py`
3. Import model in `alembic/env.py` to register with migrations
4. Create migration: `alembic revision --autogenerate -m "Description"`
5. Apply migration: `alembic upgrade head`

### Adding a New Scanner

1. Create scanner class in `app/integrations/` implementing `VulnerabilityScanner`
2. Implement `async def scan(self, repo_path: str) -> ScannerOutput`
3. Add scanner to `ScannerOrchestrator.__init__()` registry
4. Update `scan_config.scanner` options in schemas

### Working with Authentication

**Creating API Keys:**
```bash
python scripts/manage_api_keys.py create "Service Name"
```

**Using API Keys in Requests:**
```bash
curl -H "Authorization: Bearer <api-key>" http://localhost:8000/v1/scan/repository
```

**Protecting Routes:**
```python
from app.middleware.auth import get_current_api_key
from app.models.auth import APIKey

@router.get("/protected")
async def protected_route(api_key: APIKey = Depends(get_current_api_key)):
    # api_key is validated and available here
    pass
```

### Code Quality and Linting

Always run lint checks before committing code. The CI pipeline enforces these standards:

```bash
# Check code formatting with Black (line length: 100)
black --check app tests

# Auto-format code
black app tests

# Check import sorting with isort
isort --check-only app tests

# Auto-sort imports
isort app tests

# Lint with flake8 (critical errors only)
flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics

# Full flake8 check (max complexity: 10, max line length: 100)
flake8 app tests --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

# Type checking with mypy
mypy app
```

**Standards:**
- Line length: 100 characters (Black and flake8)
- Import sorting: isort with default profile
- Cyclomatic complexity: Max 10 per function
- Critical flake8 checks (E9, F63, F7, F82) must pass

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run tests in watch mode
pytest-watch
```

### Database Operations

```bash
# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (development only)
alembic downgrade base
alembic upgrade head
```

### Environment Configuration

Key environment variables (set in `.env`):
- `DATABASE_URL`: PostgreSQL connection string
- `GITHUB_TOKEN`: GitHub personal access token (required for API)
- `OSV_SCANNER_PATH`: Path to osv-scanner binary (default: `osv-scanner`)
- `SCAN_CACHE_TTL_HOURS`: Cache TTL in hours (default: 12)
- `SCAN_CACHE_MAX_SIZE`: Max cached items (default: 1000)

## Code Patterns and Conventions

### Async/Await
- Use `async def` for route handlers and I/O operations
- Use `await` for httpx requests, subprocess execution, database queries
- Use `asyncio.gather()` for parallel operations

### Error Handling
- Raise `HTTPException` from FastAPI for API errors
- Use appropriate status codes: 400 (bad request), 401 (unauthorized), 404 (not found), 408 (timeout), 429 (rate limit), 500 (internal error)
- Log errors before raising exceptions

### Database Sessions
- Use `Depends(get_db)` for route handlers
- Always use context managers or try/finally for session cleanup in scripts
- Commit explicitly after writes

### Pydantic Models
- Use `BaseModel` for request/response schemas
- Use `Field()` for validation and documentation
- Keep schemas in `app/schemas/`

### Type Hints
- Always use type hints for function parameters and return values
- Use `Optional[T]` for nullable fields
- Use `List[T]`, `Dict[K, V]` for collections

## Testing Patterns

### Route Testing
```python
def test_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
```

### Database Testing
```python
def test_model(db_session):
    scan = RepositoryScan(id="test-id", ...)
    db_session.add(scan)
    db_session.commit()
    assert scan.id == "test-id"
```

### Mocking External Services
```python
@pytest.fixture
def mock_github_client(monkeypatch):
    async def mock_get_repository(*args):
        return {"default_branch": "main"}
    monkeypatch.setattr("app.clients.github.GitHubClient.get_repository", mock_get_repository)
```

## Debugging Tips

### Check Scanner Availability
```bash
which osv-scanner
osv-scanner --version
```

### Test GitHub Token
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
```

### Check Database Connection
```bash
psql $DATABASE_URL -c "SELECT version();"
```

### View API Logs
```bash
# Run with debug logging
DEBUG=true uvicorn app.main:app --reload
```

### Interactive API Testing
Visit `http://localhost:8000/docs` for Swagger UI with interactive API testing.

## Security Considerations

- API keys are hashed with SHA-256 before storage
- Never log or return raw API keys
- Validate all user inputs with Pydantic schemas
- Use parameterized queries (SQLAlchemy handles this)
- Clean up cloned repositories after scanning
- Rate limit API endpoints (configured per API key)

## Performance Considerations

- Scanner orchestrator runs scanners in parallel with `asyncio.gather()`
- Results are cached for 12 hours per commit SHA
- Database queries use indexes on common filters (owner, name, scanned_at)
- Clone repositories with `--depth 1` for faster cloning
- Set scan timeout (default 60s) to prevent long-running operations

## Common Gotchas

1. **OSV Scanner not found**: Ensure `osv-scanner` is installed and in PATH or set `OSV_SCANNER_PATH`
2. **GitHub rate limiting**: Use a personal access token in `GITHUB_TOKEN`
3. **Database connection errors**: Verify PostgreSQL is running and `DATABASE_URL` is correct
4. **Cache not working**: Cache is in-memory, restarting the app clears it
5. **API key authentication failing**: Ensure using `Authorization: Bearer <key>` header format
6. **Async context errors**: Always `await` async functions and use `async with` for async context managers

## Useful Commands

```bash
# Start development server
uvicorn app.main:app --reload

# Create API key
python scripts/manage_api_keys.py create "Dev Key"

# List API keys
python scripts/manage_api_keys.py list

# Run example scan
export OSS_HEALTH_API_KEY='your-key'
python scripts/example_scan.py

# Run full lint check (as in CI)
black --check app tests && \
isort --check-only app tests && \
flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics && \
flake8 app tests --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

# Auto-fix formatting issues
black app tests
isort app tests

# Type checking
mypy app

# Database shell
psql $DATABASE_URL
```
