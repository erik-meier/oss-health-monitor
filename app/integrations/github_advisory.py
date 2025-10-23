"""GitHub Security Advisory Database integration."""

import time
from typing import List, Optional

import httpx

from app.config import get_settings
from app.integrations.base import ScannerOutput, VulnerabilityScanner


class GitHubAdvisoryScanner(VulnerabilityScanner):
    """Scanner using GitHub Security Advisory Database API."""

    def __init__(self, token: Optional[str] = None, timeout: int = 60):
        """
        Initialize GitHub Advisory scanner.

        Args:
            token: GitHub API token (uses config default if not provided)
            timeout: API request timeout in seconds
        """
        settings = get_settings()
        self.token = token or settings.github_token
        self.base_url = "https://api.github.com/graphql"
        self.timeout = timeout

    async def scan(self, repo_path: str) -> ScannerOutput:
        """
        Scan repository by querying GitHub Advisory API.

        This is a simplified implementation that would need to:
        1. Parse dependency manifests in repo_path
        2. Query GitHub Advisory API for each package
        3. Match versions against advisory ranges

        For now, returns empty results as a placeholder.

        Args:
            repo_path: Path to repository root

        Returns:
            ScannerOutput with vulnerabilities found
        """
        start_time = time.time()

        try:
            # Placeholder implementation
            # In production, this would:
            # 1. Parse package manifests (requirements.txt, package.json, etc.)
            # 2. Query GitHub Advisory Database for each package
            # 3. Check if installed versions are affected

            vulnerabilities = []

            # For now, return empty successful scan
            execution_time = int((time.time() - start_time) * 1000)

            return ScannerOutput(
                status="completed",
                vulnerabilities=vulnerabilities,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return ScannerOutput(
                status="failed",
                vulnerabilities=[],
                execution_time_ms=execution_time,
                error_message=str(e),
            )

    async def _query_advisory_for_package(self, ecosystem: str, package_name: str) -> List[dict]:
        """
        Query GitHub Advisory Database for a specific package.

        Args:
            ecosystem: Package ecosystem (e.g., 'PyPI', 'npm')
            package_name: Package name

        Returns:
            List of advisory data
        """
        # GraphQL query to fetch advisories
        query = """
        query($ecosystem: SecurityAdvisoryEcosystem!, $package: String!) {
          securityVulnerabilities(
            first: 100,
            ecosystem: $ecosystem,
            package: $package
          ) {
            edges {
              node {
                advisory {
                  ghsaId
                  summary
                  severity
                  publishedAt
                  cvss {
                    score
                  }
                  identifiers {
                    type
                    value
                  }
                }
                vulnerableVersionRange
                firstPatchedVersion {
                  identifier
                }
                package {
                  name
                  ecosystem
                }
              }
            }
          }
        }
        """

        variables = {
            "ecosystem": ecosystem.upper(),
            "package": package_name,
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            edges = data.get("data", {}).get("securityVulnerabilities", {}).get("edges", [])
            return [edge["node"] for edge in edges]
