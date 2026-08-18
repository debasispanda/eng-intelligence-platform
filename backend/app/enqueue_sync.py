import argparse

from app.queue import enqueue_sync


def main() -> None:
    parser = argparse.ArgumentParser(description="Enqueue an ingestion synchronization job.")
    parser.add_argument("provider", choices=("github", "jira"))
    args = parser.parse_args()

    job = enqueue_sync(args.provider)
    print(f"Enqueued {args.provider} ingestion job {job.id}.")


if __name__ == "__main__":
    main()
