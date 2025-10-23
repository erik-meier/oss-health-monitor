"""GitHub API client for repository operations."""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings


class GitHubClient:
    """Client for interacting with GitHub API and repositories."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, uses settings if not provided)
        """
        settings = get_settings()
        self.token = token or settings.github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OSS-Health-Monitor/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    async def get_repository(self, owner: str, name: str) -> Dict[str, Any]:
        """
        Get repository metadata.

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Repository metadata dict

        Raises:
            httpx.HTTPStatusError: If repository not found or API error
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{name}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_commit(self, owner: str, name: str, ref: str) -> Dict[str, Any]:
        """
        Get commit information for a specific ref.

        Args:
            owner: Repository owner
            name: Repository name
            ref: Git ref (branch, tag, or commit SHA)

        Returns:
            Commit metadata dict with 'sha' field
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{name}/commits/{ref}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_default_branch(self, owner: str, name: str) -> str:
        """
        Get the default branch name for a repository.

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Default branch name (e.g., 'main', 'master')
        """
        repo_data = await self.get_repository(owner, name)
        return repo_data.get("default_branch", "main")

    async def clone_repository(
        self, owner: str, name: str, ref: str, target_dir: Optional[Path] = None
    ) -> Path:
        """
        Clone a repository to a temporary directory.

        Args:
            owner: Repository owner
            name: Repository name
            ref: Git ref to checkout
            target_dir: Optional target directory (creates temp dir if not provided)

        Returns:
            Path to cloned repository

        Raises:
            RuntimeError: If git clone fails
        """
        if target_dir is None:
            target_dir = Path(tempfile.mkdtemp(prefix=f"{owner}_{name}_"))

        clone_url = f"https://github.com/{owner}/{name}.git"

        # Use git clone with depth 1 for efficiency
        process = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            ref,
            clone_url,
            str(target_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {stderr.decode()}")

        return target_dir

    async def get_dependency_files(self, repo_path: Path) -> List[Path]:
        """
        Find dependency manifest files in a repository.

        Args:
            repo_path: Path to repository root

        Returns:
            List of paths to dependency files
        """
        dependency_files = []

        # Common dependency file patterns
        patterns = [
            "requirements.txt",
            "requirements-*.txt",
            "Pipfile",
            "Pipfile.lock",
            "pyproject.toml",
            "poetry.lock",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "go.mod",
            "go.sum",
            "Cargo.toml",
            "Cargo.lock",
            "Gemfile",
            "Gemfile.lock",
            "composer.json",
            "composer.lock",
        ]

        for pattern in patterns:
            if "*" in pattern:
                dependency_files.extend(repo_path.glob(pattern))
            else:
                file_path = repo_path / pattern
                if file_path.exists():
                    dependency_files.append(file_path)

        return dependency_files

    def cleanup_repository(self, repo_path: Path) -> None:
        """
        Remove a cloned repository directory.

        Args:
            repo_path: Path to repository to remove
        """
        if repo_path.exists():
            shutil.rmtree(repo_path)
