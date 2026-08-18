import pytest

from app.enqueue_sync import main as enqueue_main
from app.queue import enqueue_sync
from app.scheduler import main as scheduler_main
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


def test_enqueue_command_prints_job_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Job:
        id = "job-123"

    monkeypatch.setattr("sys.argv", ["enqueue_sync", "jira"])
    monkeypatch.setattr("app.enqueue_sync.enqueue_sync", lambda provider: Job())

    enqueue_main()

    assert capsys.readouterr().out == "Enqueued jira ingestion job job-123.\n"


def test_scheduler_enqueues_both_providers_each_cycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers: list[str] = []

    def fake_enqueue(provider: str, _settings: object) -> None:
        providers.append(provider)

    def stop_after_cycle(_seconds: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("app.scheduler.enqueue_sync", fake_enqueue)
    monkeypatch.setattr("app.scheduler.sleep", stop_after_cycle)

    with pytest.raises(KeyboardInterrupt):
        scheduler_main()

    assert providers == ["github", "jira"]


def test_redis_connection_preserves_binary_rq_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRedis:
        pass

    captured: dict[str, object] = {}

    def fake_from_url(url: str, **kwargs: object) -> FakeRedis:
        captured["url"] = url
        captured.update(kwargs)
        return FakeRedis()

    monkeypatch.setattr("app.queue.Redis.from_url", fake_from_url)

    from app.queue import get_redis_connection

    get_redis_connection()

    assert captured["decode_responses"] is False
