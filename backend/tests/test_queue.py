import pytest

from app.core.config import Settings
from app.enqueue_sync import main as enqueue_main
from app.queue import enqueue_sync
from app.scheduler import configured_providers
from app.scheduler import main as scheduler_main


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[object] = []

    def enqueue(self, job: object, *args: object) -> str:
        self.enqueued.append((job, *args))
        return "job-id"


class FakeRedis:
    def set(self, *_args: object, **_kwargs: object) -> bool:
        return True


class BusyRedis(FakeRedis):
    def set(self, *_args: object, **_kwargs: object) -> bool:
        return False


@pytest.mark.parametrize(
    "provider",
    [
        "github",
        "jira",
    ],
)
def test_enqueue_sync_selects_provider_job(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
) -> None:
    queue = FakeQueue()
    monkeypatch.setattr("app.queue.get_ingestion_queue", lambda _settings=None: queue)
    monkeypatch.setattr("app.queue.get_redis_connection", lambda _settings=None: FakeRedis())

    assert enqueue_sync(provider) == "job-id"
    assert queue.enqueued[0][1] == provider


def test_enqueue_sync_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported ingestion provider"):
        enqueue_sync("unknown")


def test_enqueue_sync_skips_provider_when_job_is_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue = FakeQueue()
    monkeypatch.setattr("app.queue.get_ingestion_queue", lambda _settings=None: queue)
    monkeypatch.setattr("app.queue.get_redis_connection", lambda _settings=None: BusyRedis())

    assert enqueue_sync("github") is None
    assert queue.enqueued == []


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

    settings = Settings(
        github_token="token",
        jira_base_url="https://jira.example.com",
        jira_email="user@example.com",
        jira_api_token="token",
        jira_project_keys="EIP",
    )

    def fake_settings() -> Settings:
        return settings

    def fake_enqueue(provider: str, _settings: object) -> None:
        providers.append(provider)

    def stop_after_cycle(_seconds: int) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("app.scheduler.enqueue_sync", fake_enqueue)
    monkeypatch.setattr("app.scheduler.get_settings", fake_settings)
    monkeypatch.setattr("app.scheduler.sleep", stop_after_cycle)

    with pytest.raises(KeyboardInterrupt):
        scheduler_main()

    assert providers == ["github", "jira"]


def test_scheduler_skips_unconfigured_providers() -> None:
    settings = Settings(database_url=None)
    settings.github_token = None
    settings.jira_base_url = None
    settings.jira_email = None
    settings.jira_api_token = None
    settings.jira_project_keys = ""

    assert configured_providers(settings) == ()


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
