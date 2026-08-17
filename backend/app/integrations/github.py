from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Build, Organization, PullRequest, Repository
from app.services.ingestion import ProviderError


class GitHubClientError(ProviderError):
    """Raised when GitHub cannot provide a usable response."""


@dataclass(frozen=True)
class GitHubRepository:
    provider_id: str
    full_name: str
    default_branch: str


@dataclass(frozen=True)
class GitHubPullRequest:
    provider_id: str
    number: int
    state: str
    opened_at: datetime
    merged_at: datetime | None


@dataclass(frozen=True)
class GitHubBuild:
    provider_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None


class GitHubClient:
    def __init__(
        self,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        page_size: int = 100,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client = http_client or httpx.Client()
        self._owns_client = http_client is None
        self._headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._api_url = api_url.rstrip("/")
        self._page_size = page_size

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def list_repositories(self) -> list[GitHubRepository]:
        payloads = self._get_pages("/user/repos")
        return [
            GitHubRepository(
                provider_id=str(item["id"]),
                full_name=item["full_name"],
                default_branch=item.get("default_branch") or "main",
            )
            for item in payloads
        ]

    def list_pull_requests(self, repository: GitHubRepository) -> list[GitHubPullRequest]:
        payloads = self._get_pages(f"/repos/{repository.full_name}/pulls?state=all")
        return [
            GitHubPullRequest(
                provider_id=str(item["id"]),
                number=item["number"],
                state="merged" if item.get("merged_at") else item["state"],
                opened_at=_parse_timestamp(item["created_at"]),
                merged_at=_parse_timestamp(item["merged_at"]) if item.get("merged_at") else None,
            )
            for item in payloads
        ]

    def list_builds(self, repository: GitHubRepository) -> list[GitHubBuild]:
        payloads = self._get_pages(f"/repos/{repository.full_name}/actions/runs")
        return [
            GitHubBuild(
                provider_id=str(item["id"]),
                status=_normalize_build_status(item["conclusion"], item["status"]),
                started_at=_parse_timestamp(item["run_started_at"] or item["created_at"]),
                completed_at=_parse_timestamp(item["updated_at"])
                if item["status"] == "completed"
                else None,
            )
            for item in payloads
        ]

    def _get_pages(self, path: str) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        page = 1
        while True:
            separator = "&" if "?" in path else "?"
            response = self._client.get(
                f"{self._api_url}{path}{separator}per_page={self._page_size}&page={page}",
                headers=self._headers,
            )
            if response.status_code >= 400:
                error = GitHubClientError(
                    f"GitHub request failed with status {response.status_code}."
                )
                error.retryable = response.status_code == 429 or response.status_code >= 500
                raise error
            payload = response.json()
            if not isinstance(payload, list):
                payload = payload.get("workflow_runs", [])
            values.extend(payload)
            if len(payload) < self._page_size:
                return values
            page += 1


class GitHubSyncService:
    def sync(self, session: Session, organization: Organization, client: GitHubClient) -> int:
        synchronized = 0
        for github_repository in client.list_repositories():
            repository = session.scalar(
                select(Repository).where(Repository.provider_id == github_repository.provider_id)
            )
            if repository is None:
                repository = Repository(
                    organization_id=organization.id,
                    provider_id=github_repository.provider_id,
                    full_name=github_repository.full_name,
                    default_branch=github_repository.default_branch,
                )
                session.add(repository)
                session.flush()
            else:
                if repository.organization_id != organization.id:
                    raise GitHubClientError(
                        "GitHub repository is already assigned to another organization."
                    )
                repository.organization_id = organization.id
                repository.full_name = github_repository.full_name
                repository.default_branch = github_repository.default_branch

            for pull_request in client.list_pull_requests(github_repository):
                self._upsert_pull_request(session, repository, pull_request)
                synchronized += 1
            for build in client.list_builds(github_repository):
                self._upsert_build(session, repository, build)
                synchronized += 1

        session.commit()
        return synchronized

    @staticmethod
    def _upsert_pull_request(
        session: Session,
        repository: Repository,
        source: GitHubPullRequest,
    ) -> None:
        record = session.scalar(select(PullRequest).where(PullRequest.provider_id == source.provider_id))
        if record is None:
            record = PullRequest(repository_id=repository.id, provider_id=source.provider_id)
            session.add(record)
        record.repository_id = repository.id
        record.number = source.number
        record.state = source.state
        record.opened_at = source.opened_at
        record.merged_at = source.merged_at

    @staticmethod
    def _upsert_build(session: Session, repository: Repository, source: GitHubBuild) -> None:
        record = session.scalar(select(Build).where(Build.provider_id == source.provider_id))
        if record is None:
            record = Build(repository_id=repository.id, provider_id=source.provider_id)
            session.add(record)
        record.repository_id = repository.id
        record.status = source.status
        record.started_at = source.started_at
        record.completed_at = source.completed_at


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _normalize_build_status(conclusion: str | None, status: str) -> str:
    if status != "completed":
        return "running"
    return "failed" if conclusion in {"failure", "cancelled", "timed_out"} else "passed"
