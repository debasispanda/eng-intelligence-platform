from time import sleep

from app.core.config import get_settings
from app.queue import enqueue_sync


def main() -> None:
    settings = get_settings()
    while True:
        for provider in ("github", "jira"):
            enqueue_sync(provider, settings)
        sleep(settings.ingestion_schedule_seconds)


if __name__ == "__main__":
    main()
