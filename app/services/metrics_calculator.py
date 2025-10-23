"""Metrics calculation service."""

import statistics
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from app.integrations.base import Vulnerability


class MetricsCalculator:
    """Calculates health metrics from scan results."""

    @staticmethod
    def calculate_metrics(
        vulnerabilities: List[Vulnerability],
        dependency_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive health metrics from vulnerabilities.

        Args:
            vulnerabilities: List of vulnerabilities found
            dependency_count: Total number of dependencies (if available)

        Returns:
            Dict with health metrics structured for database storage
        """
        # Vulnerability statistics
        total_vulnerabilities = len(vulnerabilities)
        unique_packages = len(set(v.package_name for v in vulnerabilities))

        # Severity breakdown
        severity_counts = Counter(v.severity for v in vulnerabilities)

        # Temporal metrics for vulnerabilities
        vuln_ages = []
        now = datetime.utcnow()

        for vuln in vulnerabilities:
            if vuln.published_at:
                age_days = (now - vuln.published_at).days
                vuln_ages.append(age_days)

        temporal_metrics = {}
        if vuln_ages:
            temporal_metrics["mean"] = statistics.mean(vuln_ages)
            temporal_metrics["median"] = statistics.median(vuln_ages)
            temporal_metrics["max"] = max(vuln_ages)
        else:
            temporal_metrics["mean"] = None
            temporal_metrics["median"] = None
            temporal_metrics["max"] = None

        # Ecosystem breakdown
        ecosystems = list(set(v.ecosystem for v in vulnerabilities if v.ecosystem))

        return {
            "dependency_stats": {
                "total_dependencies": dependency_count,
                "direct_dependencies": 0,  # Would need manifest parsing
                "transitive_dependencies": 0,  # Would need manifest parsing
                "ecosystems": ecosystems,
            },
            "vulnerability_stats": {
                "total_vulnerabilities": total_vulnerabilities,
                "unique_packages_affected": unique_packages,
                "by_severity": {
                    "CRITICAL": severity_counts.get("CRITICAL", 0),
                    "HIGH": severity_counts.get("HIGH", 0),
                    "MODERATE": severity_counts.get("MODERATE", 0),
                    "LOW": severity_counts.get("LOW", 0),
                },
            },
            "maintenance_indicators": {
                "outdated_dependencies": 0,  # Would need package registry queries
                "dependencies_behind_major": 0,
                "dependencies_behind_minor": 0,
                "mean_dependency_age_days": None,
                "oldest_dependency_age_days": None,
            },
            "temporal_metrics": {
                "unfixed_vulnerability_age_days": temporal_metrics,
            },
        }

    @staticmethod
    def metrics_to_db_model(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert metrics dict to database model fields.

        Args:
            metrics: Metrics from calculate_metrics()

        Returns:
            Dict with fields matching ScanMetrics model
        """
        dep_stats = metrics.get("dependency_stats", {})
        vuln_stats = metrics.get("vulnerability_stats", {})
        maint = metrics.get("maintenance_indicators", {})
        temporal = metrics.get("temporal_metrics", {}).get("unfixed_vulnerability_age_days", {})

        by_severity = vuln_stats.get("by_severity", {})

        return {
            "total_dependencies": dep_stats.get("total_dependencies", 0),
            "direct_dependencies": dep_stats.get("direct_dependencies", 0),
            "transitive_dependencies": dep_stats.get("transitive_dependencies", 0),
            "total_vulnerabilities": vuln_stats.get("total_vulnerabilities", 0),
            "unique_packages_affected": vuln_stats.get("unique_packages_affected", 0),
            "critical_severity_count": by_severity.get("CRITICAL", 0),
            "high_severity_count": by_severity.get("HIGH", 0),
            "moderate_severity_count": by_severity.get("MODERATE", 0),
            "low_severity_count": by_severity.get("LOW", 0),
            "outdated_dependencies": maint.get("outdated_dependencies", 0),
            "dependencies_behind_major": maint.get("dependencies_behind_major", 0),
            "dependencies_behind_minor": maint.get("dependencies_behind_minor", 0),
            "mean_dependency_age_days": maint.get("mean_dependency_age_days"),
            "oldest_dependency_age_days": maint.get("oldest_dependency_age_days"),
            "mean_unfixed_vuln_age_days": temporal.get("mean"),
            "median_unfixed_vuln_age_days": temporal.get("median"),
            "max_unfixed_vuln_age_days": temporal.get("max"),
        }
