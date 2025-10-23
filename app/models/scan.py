"""Database models for repository scans and vulnerabilities."""

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class RepositoryScan(Base):
    """Represents a security scan of a repository at a point in time."""

    __tablename__ = "repository_scans"

    id = Column(String, primary_key=True)  # UUID
    repository_owner = Column(String, nullable=False, index=True)
    repository_name = Column(String, nullable=False, index=True)
    repository_ref = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)

    status = Column(
        SQLEnum("pending", "in_progress", "completed", "failed", name="scan_status"),
        nullable=False,
        index=True,
    )
    scanned_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    scan_config = Column(JSON, nullable=True)  # Scanner options used
    scanner_results = Column(JSON, nullable=True)  # Execution metadata from each scanner

    # Relationships
    vulnerabilities = relationship(
        "ScanVulnerability",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
    metrics = relationship(
        "ScanMetrics",
        back_populates="scan",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_repo_scan_time", "repository_owner", "repository_name", "scanned_at"),
    )


class ScanVulnerability(Base):
    """Represents a vulnerability found in a repository scan."""

    __tablename__ = "scan_vulnerabilities"

    id = Column(Integer, primary_key=True)
    scan_id = Column(String, ForeignKey("repository_scans.id"), nullable=False, index=True)

    package_name = Column(String, nullable=False)
    package_version = Column(String, nullable=False)
    ecosystem = Column(String, nullable=False)

    vulnerability_id = Column(String, nullable=False)  # GHSA-xxx or CVE-xxx
    cve_id = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    cvss_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)

    fixed_version = Column(String, nullable=True)
    scanner_source = Column(String, nullable=False)  # "osv", "github"

    scan = relationship("RepositoryScan", back_populates="vulnerabilities")

    __table_args__ = (Index("idx_vuln_package", "package_name", "vulnerability_id"),)


class ScanMetrics(Base):
    """Aggregated health metrics for time-series analysis."""

    __tablename__ = "scan_metrics"

    id = Column(Integer, primary_key=True)
    scan_id = Column(String, ForeignKey("repository_scans.id"), nullable=False, unique=True)

    # Dependency statistics
    total_dependencies = Column(Integer, nullable=False, default=0)
    direct_dependencies = Column(Integer, nullable=False, default=0)
    transitive_dependencies = Column(Integer, nullable=False, default=0)

    # Vulnerability statistics
    total_vulnerabilities = Column(Integer, nullable=False, default=0)
    unique_packages_affected = Column(Integer, nullable=False, default=0)
    critical_severity_count = Column(Integer, nullable=False, default=0)
    high_severity_count = Column(Integer, nullable=False, default=0)
    moderate_severity_count = Column(Integer, nullable=False, default=0)
    low_severity_count = Column(Integer, nullable=False, default=0)

    # Maintenance indicators
    outdated_dependencies = Column(Integer, nullable=False, default=0)
    dependencies_behind_major = Column(Integer, nullable=False, default=0)
    dependencies_behind_minor = Column(Integer, nullable=False, default=0)
    mean_dependency_age_days = Column(Float, nullable=True)
    oldest_dependency_age_days = Column(Integer, nullable=True)

    # Temporal metrics
    mean_unfixed_vuln_age_days = Column(Float, nullable=True)
    median_unfixed_vuln_age_days = Column(Float, nullable=True)
    max_unfixed_vuln_age_days = Column(Integer, nullable=True)

    scan = relationship("RepositoryScan", back_populates="metrics")
