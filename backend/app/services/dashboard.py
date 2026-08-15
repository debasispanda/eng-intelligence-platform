from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Build, Epic, Issue, PullRequest, Release, Repository, User
from app.schemas.dashboard import (
    DashboardOverview,
    EpicTimelineRow,
    HotRepositories,
    HotRepository,
    KpiCard,
    ReleaseRow,
    UserProfile,
)

WEEK = timedelta(days=7)
DAY = timedelta(days=1)


class DashboardService:
    def get_overview(
        self,
        session: Session,
        organization_id: UUID,
        *,
        now: datetime | None = None,
    ) -> DashboardOverview:
        reference_time = now or datetime.now(UTC)
        profile = self._profile(session, organization_id)

        if not self._has_dashboard_data(session, organization_id):
            return DashboardOverview(
                app_title="Engineering Intelligence",
                profile=profile,
                kpis=[],
                releases=[],
                off_timeline_epics=[],
                hot_repositories=HotRepositories(most_active=[], most_failed=[]),
            )

        return DashboardOverview(
            app_title="Engineering Intelligence",
            profile=profile,
            kpis=self._kpis(session, organization_id, reference_time),
            releases=self._releases(session, organization_id),
            off_timeline_epics=self._epics(session, organization_id),
            hot_repositories=HotRepositories(
                most_active=self._most_active(session, organization_id, reference_time),
                most_failed=self._most_failed(session, organization_id, reference_time),
            ),
        )

    def _profile(self, session: Session, organization_id: UUID) -> UserProfile:
        user = session.scalar(
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.created_at, User.id)
            .limit(1)
        )
        if user is None:
            raise LookupError("The organization has no dashboard profile.")

        return UserProfile(
            name=user.name,
            role=user.role,
            email=user.email,
            avatar_initials=user.avatar_initials,
        )

    def _has_dashboard_data(self, session: Session, organization_id: UUID) -> bool:
        source_queries = (
            select(PullRequest.id)
            .join(Repository)
            .where(Repository.organization_id == organization_id)
            .limit(1),
            select(Build.id).join(Repository).where(Repository.organization_id == organization_id).limit(1),
            select(Issue.id).where(Issue.organization_id == organization_id).limit(1),
            select(Release.id).where(Release.organization_id == organization_id).limit(1),
            select(Epic.id).where(Epic.organization_id == organization_id).limit(1),
        )
        return any(session.scalar(query) is not None for query in source_queries)

    def _kpis(
        self,
        session: Session,
        organization_id: UUID,
        now: datetime,
    ) -> list[KpiCard]:
        week_start = now - WEEK
        previous_week_start = week_start - WEEK
        yesterday = now - DAY
        day_before_yesterday = yesterday - DAY

        open_prs = self._count_pull_requests(
            session,
            organization_id,
            PullRequest.state == "open",
        )
        opened_this_week = self._count_pull_requests(
            session,
            organization_id,
            PullRequest.opened_at >= week_start,
            PullRequest.opened_at < now,
        )
        opened_last_week = self._count_pull_requests(
            session,
            organization_id,
            PullRequest.opened_at >= previous_week_start,
            PullRequest.opened_at < week_start,
        )
        merged_this_week = self._count_pull_requests(
            session,
            organization_id,
            PullRequest.merged_at >= week_start,
            PullRequest.merged_at < now,
        )
        merged_last_week = self._count_pull_requests(
            session,
            organization_id,
            PullRequest.merged_at >= previous_week_start,
            PullRequest.merged_at < week_start,
        )
        failed_this_week = self._count_builds(
            session,
            organization_id,
            Build.status == "failed",
            Build.completed_at >= week_start,
            Build.completed_at < now,
        )
        failed_last_week = self._count_builds(
            session,
            organization_id,
            Build.status == "failed",
            Build.completed_at >= previous_week_start,
            Build.completed_at < week_start,
        )
        blocked_issues = self._count_issues(session, organization_id, Issue.status == "blocked")
        blocked_since_yesterday = self._count_issues(
            session,
            organization_id,
            Issue.status == "blocked",
            Issue.created_at >= yesterday,
            Issue.created_at < now,
        )
        blocked_previous_day = self._count_issues(
            session,
            organization_id,
            Issue.status == "blocked",
            Issue.created_at >= day_before_yesterday,
            Issue.created_at < yesterday,
        )

        return [
            self._kpi("Open PRs", open_prs, opened_this_week - opened_last_week, "this week"),
            self._kpi("Merged PRs", merged_this_week, merged_this_week - merged_last_week, "this week"),
            self._kpi(
                "Failed Builds",
                failed_this_week,
                failed_this_week - failed_last_week,
                "since last week",
            ),
            self._kpi(
                "Blocked Tickets",
                blocked_issues,
                blocked_since_yesterday - blocked_previous_day,
                "since yesterday",
            ),
        ]

    @staticmethod
    def _kpi(title: str, value: int, difference: int, period: str) -> KpiCard:
        trend = "up" if difference > 0 else "down" if difference < 0 else "flat"
        return KpiCard(
            title=title,
            value=str(value),
            delta=f"{difference:+d} {period}",
            trend=trend,
        )

    @staticmethod
    def _count_pull_requests(
        session: Session,
        organization_id: UUID,
        *conditions: object,
    ) -> int:
        return DashboardService._count_for_repository_source(
            session,
            organization_id,
            PullRequest,
            *conditions,
        )

    @staticmethod
    def _count_builds(session: Session, organization_id: UUID, *conditions: object) -> int:
        return DashboardService._count_for_repository_source(
            session,
            organization_id,
            Build,
            *conditions,
        )

    @staticmethod
    def _count_for_repository_source(
        session: Session,
        organization_id: UUID,
        model: type[PullRequest] | type[Build],
        *conditions: object,
    ) -> int:
        query = (
            select(func.count(model.id))
            .join(Repository, model.repository_id == Repository.id)
            .where(Repository.organization_id == organization_id, *conditions)
        )
        return session.scalar(query) or 0

    @staticmethod
    def _count_issues(session: Session, organization_id: UUID, *conditions: object) -> int:
        return session.scalar(
            select(func.count(Issue.id)).where(Issue.organization_id == organization_id, *conditions)
        ) or 0

    @staticmethod
    def _releases(session: Session, organization_id: UUID) -> list[ReleaseRow]:
        releases = session.scalars(
            select(Release)
            .where(Release.organization_id == organization_id)
            .order_by(Release.target_date, Release.name)
        )
        return [
            ReleaseRow(
                name=release.name,
                owner=release.owner,
                status=release.status,
                completion=release.completion,
                date=release.target_date,
            )
            for release in releases
        ]

    @staticmethod
    def _epics(session: Session, organization_id: UUID) -> list[EpicTimelineRow]:
        epics = session.scalars(
            select(Epic)
            .where(Epic.organization_id == organization_id, Epic.delayed_by_days > 0)
            .order_by(Epic.delayed_by_days.desc(), Epic.title)
        )
        return [
            EpicTimelineRow(
                epic=epic.title,
                owner=epic.owner,
                delayed_by_days=epic.delayed_by_days,
                risk=epic.risk,
            )
            for epic in epics
        ]

    @staticmethod
    def _most_active(
        session: Session,
        organization_id: UUID,
        now: datetime,
    ) -> list[HotRepository]:
        return DashboardService._rank_repositories(
            session,
            organization_id,
            PullRequest,
            PullRequest.opened_at >= now - WEEK,
            PullRequest.opened_at < now,
            label="PRs this week",
        )

    @staticmethod
    def _most_failed(
        session: Session,
        organization_id: UUID,
        now: datetime,
    ) -> list[HotRepository]:
        return DashboardService._rank_repositories(
            session,
            organization_id,
            Build,
            Build.status == "failed",
            Build.completed_at >= now - WEEK,
            Build.completed_at < now,
            label="failed builds",
        )

    @staticmethod
    def _rank_repositories(
        session: Session,
        organization_id: UUID,
        model: type[PullRequest] | type[Build],
        *conditions: object,
        label: str,
    ) -> list[HotRepository]:
        metric = func.count(model.id).label("metric")
        query: Select[tuple[str, int]] = (
            select(Repository.full_name, metric)
            .join(model, model.repository_id == Repository.id)
            .where(Repository.organization_id == organization_id, *conditions)
            .group_by(Repository.id, Repository.full_name)
            .order_by(metric.desc(), Repository.full_name)
            .limit(4)
        )
        return [
            HotRepository(repository=repository, metric=count, label=label)
            for repository, count in session.execute(query)
        ]
