"""Scanner orchestration service."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.integrations import (
    GitHubAdvisoryScanner,
    OSVScanner,
    ScannerOutput,
    Vulnerability,
    VulnerabilityScanner,
)


class ScannerOrchestrator:
    """Coordinates multiple vulnerability scanners and normalizes results."""

    def __init__(self, scanners: Optional[List[VulnerabilityScanner]] = None):
        """
        Initialize orchestrator with scanners.

        Args:
            scanners: List of scanner instances (creates defaults if not provided)
        """
        if scanners is None:
            self.scanners = {
                "osv": OSVScanner(),
                "github": GitHubAdvisoryScanner(),
            }
        else:
            self.scanners = {scanner.__class__.__name__.lower(): scanner for scanner in scanners}

    async def scan_repository(
        self,
        repo_path: Path,
        scanner_preference: str = "both",
    ) -> Dict[str, Any]:
        """
        Orchestrate scanning of a repository.

        Args:
            repo_path: Path to repository root
            scanner_preference: Which scanner(s) to use ("osv", "github", "both")

        Returns:
            Dict with scanner results and deduplicated vulnerabilities
        """
        scanner_results = {}
        all_vulnerabilities = []

        # Determine which scanners to run
        scanners_to_run = []
        if scanner_preference in ["osv", "both"]:
            if "osv" in self.scanners:
                scanners_to_run.append(("osv", self.scanners["osv"]))

        if scanner_preference in ["github", "both"]:
            if "github" in self.scanners:
                scanners_to_run.append(("github", self.scanners["github"]))

        # Run scanners in parallel
        tasks = []
        for name, scanner in scanners_to_run:
            tasks.append(self._run_scanner(name, scanner, str(repo_path)))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for (name, _), result in zip(scanners_to_run, results):
                if isinstance(result, Exception):
                    scanner_results[name] = {
                        "status": "failed",
                        "vulnerabilities_found": 0,
                        "execution_time_ms": 0,
                        "error": str(result),
                    }
                else:
                    scanner_output: ScannerOutput = result
                    scanner_results[name] = {
                        "status": scanner_output.status,
                        "vulnerabilities_found": len(scanner_output.vulnerabilities),
                        "execution_time_ms": scanner_output.execution_time_ms,
                    }
                    if scanner_output.error_message:
                        scanner_results[name]["error"] = scanner_output.error_message

                    all_vulnerabilities.extend(scanner_output.vulnerabilities)

        # Deduplicate vulnerabilities
        deduplicated_vulnerabilities = self._deduplicate_vulnerabilities(all_vulnerabilities)

        return {
            "scanner_results": scanner_results,
            "vulnerabilities": deduplicated_vulnerabilities,
        }

    async def _run_scanner(
        self, name: str, scanner: VulnerabilityScanner, repo_path: str
    ) -> ScannerOutput:
        """Run a single scanner."""
        return await scanner.scan(repo_path)

    def _deduplicate_vulnerabilities(
        self, vulnerabilities: List[Vulnerability]
    ) -> List[Vulnerability]:
        """
        Deduplicate vulnerabilities found by multiple scanners.

        Strategy:
        1. If CVE ID is present, use it as primary key
        2. Otherwise, use vulnerability_id as key
        3. Prefer vulnerability with more complete data

        Args:
            vulnerabilities: List of vulnerabilities from all scanners

        Returns:
            Deduplicated list of vulnerabilities
        """
        seen = {}

        for vuln in vulnerabilities:
            # Create deduplication key
            if vuln.cve_id:
                key = (vuln.package_name, vuln.package_version, vuln.cve_id)
            else:
                key = (vuln.package_name, vuln.package_version, vuln.vulnerability_id)

            # Keep vulnerability if new or has more data
            if key not in seen:
                seen[key] = vuln
            else:
                existing = seen[key]
                # Prefer vulnerability with CVSS score if one is missing
                if vuln.cvss_score and not existing.cvss_score:
                    seen[key] = vuln
                # Prefer vulnerability with fixed version if one is missing
                elif vuln.fixed_version and not existing.fixed_version:
                    seen[key] = vuln
                # Prefer vulnerability with summary if one is missing
                elif vuln.summary and not existing.summary:
                    seen[key] = vuln

        return list(seen.values())
