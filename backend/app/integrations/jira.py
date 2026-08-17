from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Epic, Issue, Organization, Release


class JiraClientError(RuntimeError):
    """Raised when Jira cannot provide a usable response."""


@dataclass(frozen=True)
class JiraIssue:
    provider_id: str
    title: str
    status: str
    issue_type: str
    owner: str
    risk: str
    delayed_by_days: int


@dataclass(frozen=True)
class JiraRelease:
    provider_id: str
    name: str
    owner: str
    status: str
    completion: int
    target_date: date


class JiraClient:
    def __init__(
        self,
        email: str,
        api_token: str,
        base_url: str,
        *,
        page_size: int = 50,
        today: date | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client = http_client or httpx.Client()
        self._owns_client = http_client is None
        self._auth = (email, api_token)
        self._base_url = base_url.rstrip("/")
        self._page_size = page_size
        self._today = today or datetime.now(UTC).date()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def list_issues(self, project_key: str) -> list[JiraIssue]:
        payloads = self._get_issue_pages(project_key)
        return [
            JiraIssue(
                provider_id=item["id"],
                title=item["fields"]["summary"],
                status=_normalize_issue_status(item["fields"].get("status", {}).get("name")),
                issue_type=item["fields"].get("issuetype", {}).get("name", "Task"),
                owner=item["fields"].get("assignee", {}).get("displayName", project_key)
                if item["fields"].get("assignee")
                else project_key,
                risk=_normalize_risk(
                    item["fields"].get("customfield_10006"),
                    item["fields"].get("labels", []),
                    delayed_by_days := _normalize_delay(
                        item["fields"].get("labels", []),
                        item["fields"].get("duedate"),
                        self._today,
                    ),
                ),
                delayed_by_days=delayed_by_days,
            )
            for item in payloads
        ]

    def list_releases(self, project_key: str) -> list[JiraRelease]:
        response = self._request(f"/rest/api/3/project/{project_key}/versions")
        releases: list[JiraRelease] = []
        for item in response.json():
            if item.get("archived"):
                continue
            target_date = item.get("releaseDate") or item.get("startDate")
            if target_date is None:
                continue
            releases.append(
                JiraRelease(
                    provider_id=str(item["id"]),
                    name=item["name"],
                    owner=project_key,
                    status=_normalize_release_status(
                        bool(item.get("released")),
                        date.fromisoformat(target_date),
                        self._today,
                    ),
                    completion=(
                        100
                        if item.get("released")
                        else self._version_completion(project_key, str(item["id"]))
                    ),
                    target_date=date.fromisoformat(target_date),
                )
            )
        return releases

    def _version_completion(self, project_key: str, version_id: str) -> int:
        issues = self._get_issue_pages(
            project_key,
            jql_suffix=f" AND fixVersion = {version_id}",
            fields="status",
        )
        if not issues:
            return 0
        completed = sum(
            issue.get("fields", {}).get("status", {}).get("statusCategory", {}).get("key")
            == "done"
            for issue in issues
        )
        return round(completed / len(issues) * 100)

    def _get_issue_pages(
        self,
        project_key: str,
        *,
        jql_suffix: str = "",
        fields: str = "summary,status,issuetype,assignee,labels,duedate,customfield_10006,customfield_10015",
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        start_at = 0
        while True:
            response = self._request(
                "/rest/api/3/search/jql",
                params={
                    "jql": f"project = {project_key}{jql_suffix}",
                    "startAt": start_at,
                    "maxResults": self._page_size,
                    "fields": fields,
                },
            )
            payload = response.json()
            page = payload.get("issues", [])
            issues.extend(page)
            if len(page) < self._page_size or payload.get("isLast", False):
                return issues
            start_at += len(page)

    def _request(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        response = self._client.get(
            f"{self._base_url}{path}",
            auth=self._auth,
            headers={"Accept": "application/json"},
            params=params,
        )
        if response.status_code >= 400:
            raise JiraClientError(f"Jira request failed with status {response.status_code}.")
        return response


class JiraSyncService:
    def sync(
        self,
        session: Session,
        organization: Organization,
        client: JiraClient,
        project_keys: list[str],
    ) -> int:
        synchronized = 0
        for project_key in project_keys:
            for issue in client.list_issues(project_key):
                self._upsert_issue_or_epic(session, organization, issue)
                synchronized += 1
            for release in client.list_releases(project_key):
                self._upsert_release(session, organization, release)
                synchronized += 1

        session.commit()
        return synchronized

    @staticmethod
    def _upsert_issue_or_epic(
        session: Session,
        organization: Organization,
        source: JiraIssue,
    ) -> None:
        if source.issue_type.lower() == "epic":
            record = session.scalar(select(Epic).where(Epic.provider_id == source.provider_id))
            if record is None:
                record = Epic(organization_id=organization.id, provider_id=source.provider_id)
                session.add(record)
            record.organization_id = organization.id
            record.title = source.title
            record.owner = source.owner
            record.delayed_by_days = source.delayed_by_days
            record.risk = source.risk
            return

        record = session.scalar(select(Issue).where(Issue.provider_id == source.provider_id))
        if record is None:
            record = Issue(organization_id=organization.id, provider_id=source.provider_id)
            session.add(record)
        record.organization_id = organization.id
        record.title = source.title
        record.status = source.status

    @staticmethod
    def _upsert_release(
        session: Session,
        organization: Organization,
        source: JiraRelease,
    ) -> None:
        record = session.scalar(select(Release).where(Release.provider_id == source.provider_id))
        if record is None:
            record = Release(organization_id=organization.id, provider_id=source.provider_id)
            session.add(record)
        record.organization_id = organization.id
        record.name = source.name
        record.owner = source.owner
        record.status = source.status
        record.completion = source.completion
        record.target_date = source.target_date


def _normalize_issue_status(status: str | None) -> str:
    if status is None:
        return "open"
    value = status.lower()
    if value in {"blocked", "impediment"}:
        return "blocked"
    if value in {"done", "closed", "resolved"}:
        return "done"
    return "open"


def _normalize_risk(
    change_risk: dict[str, Any] | str | None,
    labels: list[str],
    delayed_by_days: int,
) -> str:
    if isinstance(change_risk, dict):
        explicit_risk = change_risk.get("value") or change_risk.get("name")
    else:
        explicit_risk = change_risk
    if explicit_risk:
        return _risk_value(str(explicit_risk))

    labels_lower = {label.lower() for label in labels}
    if "risk-high" in labels_lower:
        return "High"
    if "risk-medium" in labels_lower:
        return "Medium"
    if delayed_by_days >= 8:
        return "High"
    if delayed_by_days >= 1:
        return "Medium"
    return "Low"


def _risk_value(value: str) -> str:
    normalized = value.lower()
    if normalized == "high":
        return "High"
    if normalized == "medium":
        return "Medium"
    return "Low"


def _normalize_delay(labels: list[str], due_date: str | None, today: date) -> int:
    for label in labels:
        if label.lower().startswith("delay-days:"):
            try:
                return max(0, int(label.split(":", 1)[1]))
            except ValueError:
                break
    if due_date is not None:
        return max(0, (today - date.fromisoformat(due_date)).days)
    return 0


def _normalize_release_status(
    released: bool,
    target_date: date,
    today: date,
) -> str:
    if released:
        return "On Track"
    days_until_target = (target_date - today).days
    if days_until_target < 0:
        return "Delayed"
    if days_until_target <= 7:
        return "At Risk"
    return "On Track"
