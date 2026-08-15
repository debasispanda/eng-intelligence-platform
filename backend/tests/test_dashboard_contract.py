import json
from pathlib import Path

from app.schemas.dashboard import DashboardOverview

FIXTURES_DIRECTORY = Path(__file__).parent / "fixtures"


def test_dashboard_overview_fixture_matches_contract() -> None:
    payload = json.loads((FIXTURES_DIRECTORY / "dashboard_overview.json").read_text())

    overview = DashboardOverview.model_validate(payload)

    assert overview.releases[0].completion == 74
    assert overview.hot_repositories.most_active[0].metric == 36
    assert overview.model_dump(mode="json", by_alias=True) == payload
