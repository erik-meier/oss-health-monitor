"""Integration modules for external vulnerability scanners."""

from app.integrations.base import ScannerOutput, Vulnerability, VulnerabilityScanner
from app.integrations.github_advisory import GitHubAdvisoryScanner
from app.integrations.osv_scanner import OSVScanner

__all__ = [
    "OSVScanner",
    "GitHubAdvisoryScanner",
    "VulnerabilityScanner",
    "ScannerOutput",
    "Vulnerability",
]
