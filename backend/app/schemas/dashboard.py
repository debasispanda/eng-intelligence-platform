from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel_case(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class UserProfile(ApiModel):
    name: str
    role: str
    email: str
    avatar_initials: str


class KpiCard(ApiModel):
    title: str
    value: str
    delta: str
    trend: Literal["up", "down", "flat"]


class ReleaseRow(ApiModel):
    name: str
    owner: str
    status: Literal["On Track", "At Risk", "Delayed"]
    completion: int = Field(ge=0, le=100)
    date: date


class EpicTimelineRow(ApiModel):
    epic: str
    owner: str
    delayed_by_days: int = Field(ge=0)
    risk: Literal["Low", "Medium", "High"]


class HotRepository(ApiModel):
    repository: str
    metric: int = Field(ge=0)
    label: str


class HotRepositories(ApiModel):
    most_active: list[HotRepository]
    most_failed: list[HotRepository]


class DashboardOverview(ApiModel):
    app_title: str
    profile: UserProfile
    kpis: list[KpiCard]
    releases: list[ReleaseRow]
    off_timeline_epics: list[EpicTimelineRow]
    hot_repositories: HotRepositories
