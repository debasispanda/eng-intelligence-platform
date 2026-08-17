import pytest

from app.queue import enqueue_sync
from app.sync_github import synchronize as synchronize_github
from app.sync_jira import synchronize as synchronize_jira


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[object] = []

    def enqueue(self, job: object) -> str:
        self.enqueued.append(job)
        return "job-id"


@pytest.mark.parametrize(
    ("provider", "expected_job"),
    [
        ("github", synchronize_github),
        ("jira", synchronize_jira),
    ],
)
def test_enqueue_sync_selects_provider_job(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    expected_job: object,
) -> None:
    queue = FakeQueue()
    monkeypatch.setattr("app.queue.get_ingestion_queue", lambda _settings=None: queue)

    assert enqueue_sync(provider) == "job-id"
    assert queue.enqueued == [expected_job]


def test_enqueue_sync_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported ingestion provider"):
        enqueue_sync("unknown")
