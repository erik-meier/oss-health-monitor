"""Base classes for vulnerability scanners."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Vulnerability:
    """Normalized vulnerability data from any scanner."""

    package_name: str
    package_version: str
    ecosystem: str
    vulnerability_id: str
    cve_id: Optional[str] = None
    severity: str = "UNKNOWN"
    cvss_score: Optional[float] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    fixed_version: Optional[str] = None
    source: str = "unknown"


@dataclass
class ScannerOutput:
    """Output from a vulnerability scanner."""

    status: str  # "completed", "failed", "timeout"
    vulnerabilities: List[Vulnerability]
    execution_time_ms: int
    error_message: Optional[str] = None
    raw_output: Optional[Dict[str, Any]] = None


class VulnerabilityScanner(ABC):
    """Abstract base class for vulnerability scanners."""

    @abstractmethod
    async def scan(self, repo_path: str) -> ScannerOutput:
        """
        Scan a repository for vulnerabilities.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            ScannerOutput with normalized vulnerability data
        """
        pass
