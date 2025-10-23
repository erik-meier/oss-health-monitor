"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RepositoryInput(BaseModel):
    """Repository information in request."""

    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    ref: Optional[str] = Field(None, description="Git ref (branch/tag/commit)")


class ScanConfig(BaseModel):
    """Scan configuration options."""

    scanner: str = Field("both", description="Scanner to use: osv, github, or both")
    include_dev_dependencies: bool = Field(False, description="Include dev dependencies")
    scan_timeout_seconds: int = Field(60, description="Scan timeout in seconds")


class ScanRequest(BaseModel):
    """Request body for repository scan."""

    repository: RepositoryInput
    scan_config: Optional[ScanConfig] = Field(default_factory=ScanConfig)


class RepositoryInfo(BaseModel):
    """Repository information in response."""

    owner: str
    name: str
    ref: str
    commit_sha: str


class ScannerResult(BaseModel):
    """Result from a single scanner."""

    status: str
    vulnerabilities_found: int
    execution_time_ms: int
    error: Optional[str] = None


class VulnerabilityResponse(BaseModel):
    """Vulnerability information in response."""

    package: str
    current_version: str
    ecosystem: str
    vulnerability: Dict[str, Any]
    fixed_version: Optional[str] = None
    source: str


class DependencyStats(BaseModel):
    """Dependency statistics."""

    total_dependencies: int
    direct_dependencies: int
    transitive_dependencies: int
    ecosystems: List[str]


class VulnerabilityStats(BaseModel):
    """Vulnerability statistics."""

    total_vulnerabilities: int
    unique_packages_affected: int
    by_severity: Dict[str, int]


class MaintenanceIndicators(BaseModel):
    """Maintenance health indicators."""

    outdated_dependencies: int
    dependencies_behind_major: int
    dependencies_behind_minor: int
    mean_dependency_age_days: Optional[float] = None
    oldest_dependency_age_days: Optional[int] = None


class TemporalMetrics(BaseModel):
    """Time-based metrics."""

    unfixed_vulnerability_age_days: Dict[str, Optional[float]]


class HealthMetrics(BaseModel):
    """Complete health metrics."""

    dependency_stats: DependencyStats
    vulnerability_stats: VulnerabilityStats
    maintenance_indicators: MaintenanceIndicators
    temporal_metrics: TemporalMetrics


class ScanResponse(BaseModel):
    """Response from scan endpoint."""

    scan_id: str
    repository: RepositoryInfo
    scanned_at: datetime
    scanner_results: Dict[str, ScannerResult]
    vulnerabilities: List[VulnerabilityResponse]
    health_metrics: HealthMetrics
