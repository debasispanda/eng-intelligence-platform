from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import create_engine_from_url, session_scope
from app.integrations.github import GitHubClient, GitHubSyncService
from app.models import Organization


def main() -> None:
    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required for GitHub synchronization.")
    if settings.github_token is None:
        raise RuntimeError("GITHUB_TOKEN is required for GitHub synchronization.")

    engine = create_engine_from_url(settings.database_url)
    client = GitHubClient(
        settings.github_token,
        api_url=settings.github_api_url,
        page_size=settings.github_page_size,
    )
    try:
        with session_scope(engine) as session:
            organization = session.scalar(
                select(Organization).where(
                    Organization.name == settings.default_organization_name
                )
            )
            if organization is None:
                raise RuntimeError(
                    "The configured dashboard organization must exist before synchronization."
                )

            synchronized = GitHubSyncService().sync(session, organization, client)
            print(f"Synchronized {synchronized} GitHub records.")
    finally:
        client.close()
        engine.dispose()


if __name__ == "__main__":
    main()
