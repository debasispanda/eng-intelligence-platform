from datetime import date
from urllib.parse import parse_qs

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.jira import JiraClient, JiraClientError, JiraSyncService
from app.models import Epic, Issue, Organization, Release


def test_jira_client_maps_issues_and_releases() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search/jql"):
            query = parse_qs(request.url.query.decode())
            start_at = query["startAt"][0]
            if "fixVersion" in query["jql"][0]:
                return httpx.Response(
                    200,
                    json={
                        "issues": [
                            {
                                "id": "version-issue-1",
                                "fields": {
                                    "status": {
                                        "statusCategory": {"key": "done"}
                                    }
                                },
                            },
                            {
                                "id": "version-issue-2",
                                "fields": {
                                    "status": {
                                        "statusCategory": {"key": "indeterminate"}
                                    }
                                },
                            },
                        ],
                        "isLast": True,
                    },
                    request=request,
                )
            issue = {
                "id": "jira-1",
                "fields": {
                    "summary": "Tenant isolation",
                    "status": {"name": "Blocked"},
                    "issuetype": {"name": "Epic"},
                    "assignee": {"displayName": "Platform Security"},
                    "labels": [],
                    "duedate": "2026-08-05",
                    "customfield_10006": None,
                }
            }
            return httpx.Response(
                200,
                json={"issues": [issue] if start_at == "0" else [], "isLast": start_at != "0"},
                request=request,
            )
        return httpx.Response(
            200,
            json=[
                {
                    "id": "version-1",
                    "name": "Platform 2.8",
                    "released": False,
                    "archived": False,
                    "releaseDate": "2026-08-20",
                }
            ],
            request=request,
        )

    client = JiraClient(
        "riley@example.com",
        "test-token",
        "https://example.atlassian.net",
        page_size=1,
        today=date(2026, 8, 17),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    issues = client.list_issues("PLATFORM")
    releases = client.list_releases("PLATFORM")
    client.close()

    assert issues[0].issue_type == "Epic"
    assert issues[0].risk == "High"
    assert issues[0].delayed_by_days == 12
    assert releases[0].target_date == date(2026, 8, 20)
    assert releases[0].status == "At Risk"
    assert releases[0].completion == 50


def test_jira_sync_is_idempotent(db_session: Session) -> None:
    organization = Organization(name="Jira Organization")
    db_session.add(organization)
    db_session.commit()

    class FakeJiraClient:
        def list_issues(self, _project_key):
            return [
                type(
                    "IssuePayload",
                    (),
                    {
                        "provider_id": "jira-1",
                        "title": "Blocked work",
                        "status": "blocked",
                        "issue_type": "Task",
                        "owner": "Platform",
                        "risk": "Low",
                        "delayed_by_days": 0,
                    },
                )(),
                type(
                    "EpicPayload",
                    (),
                    {
                        "provider_id": "jira-2",
                        "title": "Delayed epic",
                        "status": "open",
                        "issue_type": "Epic",
                        "owner": "Platform",
                        "risk": "High",
                        "delayed_by_days": 4,
                    },
                )(),
            ]

        def list_releases(self, _project_key):
            return [
                type(
                    "ReleasePayload",
                    (),
                    {
                        "provider_id": "version-1",
                        "name": "Platform 2.8",
                        "owner": "PLATFORM",
                        "status": "On Track",
                        "completion": 0,
                        "target_date": date(2026, 8, 20),
                    },
                )()
            ]

    service = JiraSyncService()
    service.sync(db_session, organization, FakeJiraClient(), ["PLATFORM"])
    service.sync(db_session, organization, FakeJiraClient(), ["PLATFORM"])

    assert len(db_session.scalars(select(Issue)).all()) == 1
    assert len(db_session.scalars(select(Epic)).all()) == 1
    assert len(db_session.scalars(select(Release)).all()) == 1


def test_jira_client_surfaces_provider_errors() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(401, json={"message": "unauthorized"}, request=request)
    )
    client = JiraClient(
        "riley@example.com",
        "test-token",
        "https://example.atlassian.net",
        http_client=httpx.Client(transport=transport),
    )

    with pytest.raises(JiraClientError, match="status 401"):
        client.list_issues("PLATFORM")

    client.close()


def test_jira_risk_prefers_explicit_value_over_derived_delay() -> None:
    from app.integrations.jira import _normalize_risk

    assert _normalize_risk({"value": "Low"}, [], 12) == "Low"
    assert _normalize_risk(None, [], 7) == "Medium"
    assert _normalize_risk(None, [], 0) == "Low"
    assert _normalize_risk(None, ["risk-medium"], 12) == "Medium"


def test_jira_release_status_uses_release_date_and_completion() -> None:
    from app.integrations.jira import _normalize_release_status

    today = date(2026, 8, 17)

    assert _normalize_release_status(True, date(2026, 8, 1), today) == "On Track"
    assert _normalize_release_status(False, date(2026, 8, 16), today) == "Delayed"
    assert _normalize_release_status(False, date(2026, 8, 20), today) == "At Risk"
    assert _normalize_release_status(False, date(2026, 8, 25), today) == "On Track"
