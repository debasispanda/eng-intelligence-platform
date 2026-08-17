from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.github import GitHubClient, GitHubClientError, GitHubSyncService
from app.models import Build, Organization, PullRequest, Repository


def test_github_client_maps_paginated_provider_payloads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        query = parse_qs(urlparse(str(request.url)).query)
        page = query["page"][0]

        if request.url.path == "/user/repos":
            payload = (
                [
                    {
                        "id": 101,
                        "full_name": "acme/platform-api",
                        "default_branch": "main",
                    }
                ]
                if page == "1"
                else []
            )
        elif request.url.path == "/repos/acme/platform-api/pulls":
            payload = (
                [
                    {
                        "id": 202,
                        "number": 7,
                        "state": "closed",
                        "created_at": "2026-08-15T10:00:00Z",
                        "merged_at": "2026-08-15T11:00:00Z",
                    }
                ]
                if page == "1"
                else []
            )
        else:
            payload = (
                {
                    "workflow_runs": [
                        {
                            "id": 303,
                            "status": "completed",
                            "conclusion": "failure",
                            "run_started_at": "2026-08-15T09:00:00Z",
                            "created_at": "2026-08-15T09:00:00Z",
                            "updated_at": "2026-08-15T09:05:00Z",
                        }
                    ]
                }
                if page == "1"
                else {"workflow_runs": []}
            )

        return httpx.Response(200, json=payload, request=request)

    client = GitHubClient(
        "test-token",
        page_size=1,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    repositories = client.list_repositories()
    pull_requests = client.list_pull_requests(repositories[0])
    builds = client.list_builds(repositories[0])
    client.close()

    assert repositories[0].provider_id == "101"
    assert pull_requests[0].state == "merged"
    assert pull_requests[0].merged_at == datetime(2026, 8, 15, 11, tzinfo=UTC)
    assert builds[0].status == "failed"


def test_github_sync_is_idempotent(db_session: Session) -> None:
    organization = Organization(name="GitHub Organization")
    db_session.add(organization)
    db_session.commit()

    class FakeGitHubClient:
        def list_repositories(self):
            return [
                type(
                    "RepositoryPayload",
                    (),
                    {
                        "provider_id": "101",
                        "full_name": "acme/platform-api",
                        "default_branch": "main",
                    },
                )()
            ]

        def list_pull_requests(self, _repository):
            return [
                type(
                    "PullRequestPayload",
                    (),
                    {
                        "provider_id": "202",
                        "number": 7,
                        "state": "open",
                        "opened_at": datetime(2026, 8, 15, tzinfo=UTC),
                        "merged_at": None,
                    },
                )()
            ]

        def list_builds(self, _repository):
            return [
                type(
                    "BuildPayload",
                    (),
                    {
                        "provider_id": "303",
                        "status": "passed",
                        "started_at": datetime(2026, 8, 15, tzinfo=UTC),
                        "completed_at": datetime(2026, 8, 15, 1, tzinfo=UTC),
                    },
                )()
            ]

    service = GitHubSyncService()
    service.sync(db_session, organization, FakeGitHubClient())
    service.sync(db_session, organization, FakeGitHubClient())

    assert db_session.scalar(select(Repository.provider_id)) == "101"
    assert db_session.scalar(select(PullRequest.provider_id)) == "202"
    assert db_session.scalar(select(Build.provider_id)) == "303"
    assert len(db_session.scalars(select(Repository)).all()) == 1
    assert len(db_session.scalars(select(PullRequest)).all()) == 1
    assert len(db_session.scalars(select(Build)).all()) == 1


def test_github_client_surfaces_provider_errors() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(403, json={"message": "rate limit"}, request=request)
    )
    client = GitHubClient("test-token", http_client=httpx.Client(transport=transport))

    with pytest.raises(GitHubClientError, match="status 403"):
        client.list_repositories()

    client.close()


def test_github_sync_rejects_cross_organization_repository(
    db_session: Session,
) -> None:
    owner = Organization(name="Repository Owner")
    other = Organization(name="Other Organization")
    db_session.add_all([owner, other])
    db_session.flush()
    db_session.add(
        Repository(
            organization_id=owner.id,
            provider_id="101",
            full_name="acme/platform-api",
            default_branch="main",
        )
    )
    db_session.commit()

    class RepositoryOnlyClient:
        def list_repositories(self):
            return [
                type(
                    "RepositoryPayload",
                    (),
                    {
                        "provider_id": "101",
                        "full_name": "acme/platform-api",
                        "default_branch": "main",
                    },
                )()
            ]

        def list_pull_requests(self, _repository):
            return []

        def list_builds(self, _repository):
            return []

    with pytest.raises(GitHubClientError, match="another organization"):
        GitHubSyncService().sync(db_session, other, RepositoryOnlyClient())
