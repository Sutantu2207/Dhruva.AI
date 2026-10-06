"""Repository Provider Abstraction for Domain 8.

Provides an extensible contract for ingesting repository metadata from GitHub, GitLab, and Bitbucket.
CRITICAL INVARIANT: Repository metrics (commits, lines of code, stars) NEVER automatically
equal skill proficiency. They serve strictly as empirical evidence inputs evaluated by the
deterministic evidence engine.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class RepositoryMetadata:
    """Safe normalized repository metadata structure."""
    provider: str  # github, gitlab, bitbucket, other
    owner: str
    repo_name: str
    normalized_url: str
    primary_language: Optional[str] = None
    detected_languages: List[str] = field(default_factory=list)
    has_readme: bool = False
    has_tests: bool = False
    has_ci_workflow: bool = False
    is_valid_url: bool = True
    metadata_details: Dict[str, Any] = field(default_factory=dict)


class BaseRepositoryProvider(ABC):
    """Abstract interface for external source code repository providers."""

    @abstractmethod
    def parse_repository_url(self, url: str) -> Optional[RepositoryMetadata]:
        """Safely parses and normalizes a repository URL without external API requirements."""
        pass


class DefaultRepositoryProvider(BaseRepositoryProvider):
    """Safe, offline-first repository metadata extractor without mandatory external API tokens."""

    # Patterns for popular Git forges
    GITHUB_REGEX = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/.*)?$")
    GITLAB_REGEX = re.compile(r"^(?:https?://)?(?:www\.)?gitlab\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/.*)?$")
    BITBUCKET_REGEX = re.compile(r"^(?:https?://)?(?:www\.)?bitbucket\.org/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/.*)?$")

    def parse_repository_url(self, url: str) -> Optional[RepositoryMetadata]:
        if not url or not isinstance(url, str):
            return None

        clean_url = url.strip()

        # 1. GitHub
        gh_match = self.GITHUB_REGEX.match(clean_url)
        if gh_match:
            owner, repo = gh_match.group(1), gh_match.group(2)
            if repo.endswith(".git"):
                repo = repo[:-4]
            return RepositoryMetadata(
                provider="github",
                owner=owner,
                repo_name=repo,
                normalized_url=f"https://github.com/{owner}/{repo}",
                has_readme=True,  # Base structural expectation
                is_valid_url=True,
                metadata_details={"platform": "GitHub", "repo_type": "public_web"},
            )

        # 2. GitLab
        gl_match = self.GITLAB_REGEX.match(clean_url)
        if gl_match:
            owner, repo = gl_match.group(1), gl_match.group(2)
            if repo.endswith(".git"):
                repo = repo[:-4]
            return RepositoryMetadata(
                provider="gitlab",
                owner=owner,
                repo_name=repo,
                normalized_url=f"https://gitlab.com/{owner}/{repo}",
                has_readme=True,
                is_valid_url=True,
                metadata_details={"platform": "GitLab", "repo_type": "public_web"},
            )

        # 3. Bitbucket
        bb_match = self.BITBUCKET_REGEX.match(clean_url)
        if bb_match:
            owner, repo = bb_match.group(1), bb_match.group(2)
            if repo.endswith(".git"):
                repo = repo[:-4]
            return RepositoryMetadata(
                provider="bitbucket",
                owner=owner,
                repo_name=repo,
                normalized_url=f"https://bitbucket.org/{owner}/{repo}",
                has_readme=True,
                is_valid_url=True,
                metadata_details={"platform": "Bitbucket", "repo_type": "public_web"},
            )

        # 4. Generic Git URL fallback
        if clean_url.startswith("http://") or clean_url.startswith("https://"):
            parts = clean_url.rstrip("/").split("/")
            repo_name = parts[-1] if parts else "repo"
            owner = parts[-2] if len(parts) >= 2 else "user"
            return RepositoryMetadata(
                provider="generic_git",
                owner=owner,
                repo_name=repo_name,
                normalized_url=clean_url,
                is_valid_url=True,
                metadata_details={"platform": "Generic Git"},
            )

        return None


repository_provider = DefaultRepositoryProvider()
