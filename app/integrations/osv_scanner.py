"""Google OSV Scanner integration."""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Optional

from app.config import get_settings
from app.integrations.base import ScannerOutput, Vulnerability, VulnerabilityScanner


class OSVScanner(VulnerabilityScanner):
    """Integration with Google OSV Scanner."""

    def __init__(self, scanner_path: Optional[str] = None, timeout: int = 60):
        """
        Initialize OSV Scanner.

        Args:
            scanner_path: Path to osv-scanner binary (uses config default if not provided)
            timeout: Scan timeout in seconds
        """
        settings = get_settings()
        self.scanner_path = scanner_path or settings.osv_scanner_path
        self.timeout = timeout

    async def scan(self, repo_path: str) -> ScannerOutput:
        """
        Scan repository using OSV Scanner.

        Args:
            repo_path: Path to repository root

        Returns:
            ScannerOutput with vulnerabilities found
        """
        start_time = time.time()

        try:
            # Execute osv-scanner with JSON output
            process = await asyncio.create_subprocess_exec(
                self.scanner_path,
                "--format",
                "json",
                "--lockfile-scan-dir",
                repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution_time = int((time.time() - start_time) * 1000)
                return ScannerOutput(
                    status="timeout",
                    vulnerabilities=[],
                    execution_time_ms=execution_time,
                    error_message="Scanner execution timed out",
                )

            execution_time = int((time.time() - start_time) * 1000)

            # OSV Scanner returns exit code 0 for no vulns, 1 for vulns found
            # Both are successful scans
            if process.returncode not in [0, 1]:
                return ScannerOutput(
                    status="failed",
                    vulnerabilities=[],
                    execution_time_ms=execution_time,
                    error_message=stderr.decode(),
                )

            # Parse JSON output
            try:
                raw_output = json.loads(stdout.decode())
            except json.JSONDecodeError:
                return ScannerOutput(
                    status="failed",
                    vulnerabilities=[],
                    execution_time_ms=execution_time,
                    error_message="Failed to parse OSV Scanner output",
                )

            vulnerabilities = self._parse_osv_output(raw_output)

            return ScannerOutput(
                status="completed",
                vulnerabilities=vulnerabilities,
                execution_time_ms=execution_time,
                raw_output=raw_output,
            )

        except FileNotFoundError:
            execution_time = int((time.time() - start_time) * 1000)
            return ScannerOutput(
                status="failed",
                vulnerabilities=[],
                execution_time_ms=execution_time,
                error_message=f"OSV Scanner not found at {self.scanner_path}",
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return ScannerOutput(
                status="failed",
                vulnerabilities=[],
                execution_time_ms=execution_time,
                error_message=str(e),
            )

    def _parse_osv_output(self, raw_output: dict) -> List[Vulnerability]:
        """
        Parse OSV Scanner JSON output into normalized vulnerabilities.

        Args:
            raw_output: Raw JSON output from OSV Scanner

        Returns:
            List of normalized Vulnerability objects
        """
        vulnerabilities = []
        results = raw_output.get("results", [])

        for result in results:
            packages = result.get("packages", [])
            for package in packages:
                package_info = self._extract_package_info(package)
                vulns = package.get("vulnerabilities", [])

                for vuln in vulns:
                    vulnerability = self._parse_vulnerability(vuln, package_info)
                    vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _extract_package_info(self, package: dict) -> dict:
        """Extract package information from OSV output."""
        return {
            "name": package.get("package", {}).get("name", "unknown"),
            "version": package.get("package", {}).get("version", "unknown"),
            "ecosystem": package.get("package", {}).get("ecosystem", "unknown"),
        }

    def _parse_vulnerability(self, vuln: dict, package_info: dict) -> Vulnerability:
        """Parse a single vulnerability from OSV output."""
        vuln_id = vuln.get("id", "unknown")
        severity, cvss_score = self._extract_severity(vuln)
        cve_id = self._extract_cve_id(vuln)
        fixed_version = self._extract_fixed_version(vuln, package_info["name"])
        published_at = self._extract_published_date(vuln)

        return Vulnerability(
            package_name=package_info["name"],
            package_version=package_info["version"],
            ecosystem=package_info["ecosystem"],
            vulnerability_id=vuln_id,
            cve_id=cve_id,
            severity=severity,
            cvss_score=cvss_score,
            summary=vuln.get("summary"),
            published_at=published_at,
            fixed_version=fixed_version,
            source="osv",
        )

    def _extract_severity(self, vuln: dict) -> tuple:
        """Extract severity and CVSS score from vulnerability data."""
        severity = "UNKNOWN"
        cvss_score = None

        for severity_entry in vuln.get("database_specific", {}).get("severity", []):
            if severity_entry.get("type") == "CVSS_V3":
                cvss_score = severity_entry.get("score")
                if cvss_score:
                    if cvss_score >= 9.0:
                        severity = "CRITICAL"
                    elif cvss_score >= 7.0:
                        severity = "HIGH"
                    elif cvss_score >= 4.0:
                        severity = "MODERATE"
                    else:
                        severity = "LOW"
                break

        return severity, cvss_score

    def _extract_cve_id(self, vuln: dict) -> Optional[str]:
        """Extract CVE ID from vulnerability aliases."""
        for alias in vuln.get("aliases", []):
            if alias.startswith("CVE-"):
                return alias
        return None

    def _extract_fixed_version(self, vuln: dict, package_name: str) -> Optional[str]:
        """Extract fixed version for the package."""
        for affected in vuln.get("affected", []):
            if affected.get("package", {}).get("name") == package_name:
                ranges = affected.get("ranges", [])
                for range_entry in ranges:
                    events = range_entry.get("events", [])
                    for event in events:
                        if "fixed" in event:
                            return event["fixed"]
        return None

    def _extract_published_date(self, vuln: dict) -> Optional[datetime]:
        """Extract publication date from vulnerability data."""
        if "published" in vuln:
            try:
                return datetime.fromisoformat(vuln["published"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        return None
