"""Scan endpoint for repository vulnerability scanning."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.clients.github import GitHubClient
from app.database import get_db
from app.middleware.auth import get_current_api_key
from app.models.auth import APIKey
from app.models.scan import RepositoryScan, ScanMetrics, ScanVulnerability
from app.schemas import (
    DependencyStats,
    HealthMetrics,
    MaintenanceIndicators,
    ScannerResult,
    ScanRequest,
    ScanResponse,
    TemporalMetrics,
    VulnerabilityResponse,
    VulnerabilityStats,
)
from app.services.cache import get_scan_cache
from app.services.metrics_calculator import MetricsCalculator
from app.services.scanner_orchestrator import ScannerOrchestrator

router = APIRouter(prefix="/v1/scan", tags=["Scan"])


@router.post("/repository", response_model=ScanResponse, status_code=status.HTTP_200_OK)
async def scan_repository(
    request: ScanRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_current_api_key),
) -> ScanResponse:
    """
    Scan a GitHub repository for security vulnerabilities.

    This endpoint triggers a comprehensive security scan of a repository,
    checking dependencies for known vulnerabilities and generating health metrics.
    Results are cached for 12 hours to avoid redundant scans.

    Args:
        request: Scan request with repository info and configuration
        db: Database session
        api_key: Authenticated API key

    Returns:
        ScanResponse with vulnerabilities and health metrics

    Raises:
        HTTPException: 404 if repository not found, 400 for invalid input,
                      408 for timeout, 500 for internal errors
    """
    repo = request.repository
    config = request.scan_config
    github_client = GitHubClient()

    try:
        # Get repository info and check cache
        repo_data, ref, commit_sha = await _get_repository_info(github_client, repo)
        cached_result = _check_cache(repo.owner, repo.name, ref, commit_sha)
        if cached_result:
            return ScanResponse(**cached_result)

        # Create scan record and execute scan
        scan_id = _create_scan_record(db, repo, ref, commit_sha, config)
        response_data = await _execute_scan(
            github_client, db, scan_id, repo, ref, commit_sha, config
        )

        # Cache and return result
        cache = get_scan_cache()
        cache.set(repo.owner, repo.name, ref, commit_sha, response_data)
        return ScanResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


async def _get_repository_info(github_client: GitHubClient, repo) -> tuple:
    """Get repository metadata and resolve ref to commit SHA."""
    try:
        repo_data = await github_client.get_repository(repo.owner, repo.name)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repo.owner}/{repo.name}",
        )

    ref = repo.ref or repo_data.get("default_branch", "main")

    try:
        commit_data = await github_client.get_commit(repo.owner, repo.name, ref)
        commit_sha = commit_data["sha"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ref: {ref}",
        )

    return repo_data, ref, commit_sha


def _check_cache(owner: str, name: str, ref: str, commit_sha: str):
    """Check if scan result is cached."""
    cache = get_scan_cache()
    return cache.get(owner, name, ref, commit_sha)


def _create_scan_record(db: Session, repo, ref: str, commit_sha: str, config) -> str:
    """Create initial scan record in database."""
    scan_id = str(uuid.uuid4())
    scan = RepositoryScan(
        id=scan_id,
        repository_owner=repo.owner,
        repository_name=repo.name,
        repository_ref=ref,
        commit_sha=commit_sha,
        status="in_progress",
        scanned_at=datetime.utcnow(),
        scan_config={
            "scanner": config.scanner,
            "include_dev_dependencies": config.include_dev_dependencies,
            "scan_timeout_seconds": config.scan_timeout_seconds,
        },
    )
    db.add(scan)
    db.commit()
    return scan_id


async def _execute_scan(
    github_client: GitHubClient, db: Session, scan_id: str, repo, ref: str, commit_sha: str, config
) -> dict:
    """Execute the vulnerability scan and store results."""
    # Clone repository
    scan = db.query(RepositoryScan).filter(RepositoryScan.id == scan_id).first()

    try:
        repo_path = await github_client.clone_repository(repo.owner, repo.name, ref)
    except Exception as e:
        scan.status = "failed"
        scan.error_message = f"Failed to clone repository: {str(e)}"
        scan.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=scan.error_message,
        )

    try:
        # Run scanners and calculate metrics
        orchestrator = ScannerOrchestrator()
        scan_results = await orchestrator.scan_repository(
            repo_path, scanner_preference=config.scanner
        )

        calculator = MetricsCalculator()
        health_metrics = calculator.calculate_metrics(scan_results["vulnerabilities"])

        # Store results in database
        _store_scan_results(db, scan, scan_id, scan_results, health_metrics, calculator)

        # Build response data
        return _build_response_data(
            scan_id, repo, ref, commit_sha, scan, scan_results, health_metrics
        )

    finally:
        github_client.cleanup_repository(repo_path)


def _store_scan_results(
    db: Session, scan, scan_id: str, scan_results: dict, health_metrics: dict, calculator
):
    """Store scan results in database."""
    scan.scanner_results = scan_results["scanner_results"]

    # Store vulnerabilities
    for vuln in scan_results["vulnerabilities"]:
        db_vuln = ScanVulnerability(
            scan_id=scan_id,
            package_name=vuln.package_name,
            package_version=vuln.package_version,
            ecosystem=vuln.ecosystem,
            vulnerability_id=vuln.vulnerability_id,
            cve_id=vuln.cve_id,
            severity=vuln.severity,
            cvss_score=vuln.cvss_score,
            summary=vuln.summary,
            published_at=vuln.published_at,
            fixed_version=vuln.fixed_version,
            scanner_source=vuln.source,
        )
        db.add(db_vuln)

    # Store metrics
    metrics_data = calculator.metrics_to_db_model(health_metrics)
    db_metrics = ScanMetrics(scan_id=scan_id, **metrics_data)
    db.add(db_metrics)

    # Update scan status
    scan.status = "completed"
    scan.completed_at = datetime.utcnow()
    db.commit()


def _build_response_data(
    scan_id: str, repo, ref: str, commit_sha: str, scan, scan_results: dict, health_metrics: dict
) -> dict:
    """Build response data structure."""
    return {
        "scan_id": scan_id,
        "repository": {
            "owner": repo.owner,
            "name": repo.name,
            "ref": ref,
            "commit_sha": commit_sha,
        },
        "scanned_at": scan.scanned_at,
        "scanner_results": {
            name: ScannerResult(**result)
            for name, result in scan_results["scanner_results"].items()
        },
        "vulnerabilities": [
            VulnerabilityResponse(
                package=v.package_name,
                current_version=v.package_version,
                ecosystem=v.ecosystem,
                vulnerability={
                    "id": v.vulnerability_id,
                    "cve_id": v.cve_id,
                    "severity": v.severity,
                    "cvss_score": v.cvss_score,
                    "summary": v.summary,
                    "published_at": v.published_at.isoformat() if v.published_at else None,
                },
                fixed_version=v.fixed_version,
                source=v.source,
            )
            for v in scan_results["vulnerabilities"]
        ],
        "health_metrics": HealthMetrics(
            dependency_stats=DependencyStats(**health_metrics["dependency_stats"]),
            vulnerability_stats=VulnerabilityStats(**health_metrics["vulnerability_stats"]),
            maintenance_indicators=MaintenanceIndicators(
                **health_metrics["maintenance_indicators"]
            ),
            temporal_metrics=TemporalMetrics(**health_metrics["temporal_metrics"]),
        ),
    }
