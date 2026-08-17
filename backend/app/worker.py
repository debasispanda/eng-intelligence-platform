from rq import Worker

from app.core.config import get_settings
from app.queue import get_ingestion_queue, get_redis_connection


def main() -> None:
    settings = get_settings()
    connection = get_redis_connection(settings)
    worker = Worker(
        [get_ingestion_queue(settings)],
        connection=connection,
    )
    worker.work()


if __name__ == "__main__":
    main()
