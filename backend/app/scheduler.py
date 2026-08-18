from time import sleep

from app.core.config import Settings, get_settings
from app.queue import enqueue_sync


def configured_providers(settings: Settings) -> tuple[str, ...]:
    providers: list[str] = []
    if settings.github_token:
        providers.append("github")
    if all(
        (
            settings.jira_base_url,
            settings.jira_email,
            settings.jira_api_token,
            settings.jira_project_keys.strip(),
        )
    ):
        providers.append("jira")
    return tuple(providers)


def main() -> None:
    settings = get_settings()
    while True:
        for provider in configured_providers(settings):
            enqueue_sync(provider, settings)
        sleep(settings.ingestion_schedule_seconds)


if __name__ == "__main__":
    main()
