#!/usr/bin/env python3
"""Example script demonstrating how to use the scan API."""

import asyncio
import httpx
import json
import os
from datetime import datetime


async def scan_repository(
    api_key: str,
    owner: str,
    name: str,
    ref: str = None,
    scanner: str = "both",
    base_url: str = "http://localhost:8000",
):
    """
    Scan a repository using the API.
    
    Args:
        api_key: API authentication key
        owner: Repository owner
        name: Repository name
        ref: Optional git ref (branch/tag/commit)
        scanner: Scanner to use (osv, github, or both)
        base_url: API base URL
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    request_body = {
        "repository": {
            "owner": owner,
            "name": name,
        },
        "scan_config": {
            "scanner": scanner,
            "include_dev_dependencies": False,
            "scan_timeout_seconds": 60,
        },
    }
    
    if ref:
        request_body["repository"]["ref"] = ref
    
    print(f"\n{'='*60}")
    print(f"Scanning: {owner}/{name}" + (f" @ {ref}" if ref else ""))
    print(f"Scanner: {scanner}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{base_url}/v1/scan/repository",
                headers=headers,
                json=request_body,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Print results
            print("✅ Scan completed successfully!\n")
            print(f"Scan ID: {result['scan_id']}")
            print(f"Scanned at: {result['scanned_at']}")
            print(f"Commit SHA: {result['repository']['commit_sha'][:8]}...\n")
            
            # Scanner results
            print("Scanner Results:")
            for scanner_name, scanner_result in result["scanner_results"].items():
                status_icon = "✅" if scanner_result["status"] == "completed" else "❌"
                print(f"  {status_icon} {scanner_name.upper()}:")
                print(f"     Status: {scanner_result['status']}")
                print(f"     Vulnerabilities: {scanner_result['vulnerabilities_found']}")
                print(f"     Execution time: {scanner_result['execution_time_ms']}ms")
            
            # Vulnerability summary
            vuln_stats = result["health_metrics"]["vulnerability_stats"]
            print(f"\nVulnerability Summary:")
            print(f"  Total vulnerabilities: {vuln_stats['total_vulnerabilities']}")
            print(f"  Packages affected: {vuln_stats['unique_packages_affected']}")
            print(f"  By severity:")
            for severity, count in vuln_stats["by_severity"].items():
                if count > 0:
                    print(f"    {severity}: {count}")
            
            # List vulnerabilities
            if result["vulnerabilities"]:
                print(f"\nDetailed Vulnerabilities:")
                for vuln in result["vulnerabilities"]:
                    severity = vuln["vulnerability"]["severity"]
                    severity_icons = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MODERATE": "🟡",
                        "LOW": "🟢",
                    }
                    icon = severity_icons.get(severity, "⚪")
                    
                    print(f"\n  {icon} {vuln['package']} v{vuln['current_version']}")
                    print(f"     ID: {vuln['vulnerability']['id']}")
                    print(f"     Severity: {severity}")
                    if vuln['vulnerability'].get('cvss_score'):
                        print(f"     CVSS: {vuln['vulnerability']['cvss_score']}")
                    if vuln['fixed_version']:
                        print(f"     Fixed in: {vuln['fixed_version']}")
                    if vuln['vulnerability'].get('summary'):
                        summary = vuln['vulnerability']['summary']
                        # Truncate long summaries
                        if len(summary) > 80:
                            summary = summary[:77] + "..."
                        print(f"     Summary: {summary}")
            else:
                print("\n✅ No vulnerabilities found!")
            
            # Dependency stats
            dep_stats = result["health_metrics"]["dependency_stats"]
            print(f"\nDependency Statistics:")
            print(f"  Total dependencies: {dep_stats['total_dependencies']}")
            print(f"  Ecosystems: {', '.join(dep_stats['ecosystems']) if dep_stats['ecosystems'] else 'None detected'}")
            
            print(f"\n{'='*60}\n")
            
            return result
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise


async def main():
    """Main function with example usage."""
    # Get API key from environment variable
    api_key = os.getenv("OSS_HEALTH_API_KEY")
    
    if not api_key:
        print("Error: OSS_HEALTH_API_KEY environment variable not set")
        print("\nUsage:")
        print("  export OSS_HEALTH_API_KEY='your-api-key'")
        print("  python scripts/example_scan.py")
        return
    
    # Example: Scan this repository
    await scan_repository(
        api_key=api_key,
        owner="erik-meier",
        name="oss-health-monitor",
        ref="main",
        scanner="osv",  # Use OSV scanner only for demo
    )
    
    # Example: Scan another repository (commented out)
    # await scan_repository(
    #     api_key=api_key,
    #     owner="psf",
    #     name="requests",
    #     scanner="both",
    # )


if __name__ == "__main__":
    asyncio.run(main())
