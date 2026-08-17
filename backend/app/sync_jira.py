from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import create_engine_from_url, session_scope
from app.integrations.jira import JiraClient, JiraSyncService
from app.models import Organization
from app.services.ingestion import run_with_retries


def main() -> None:
    settings = get_settings()
    if not all((settings.database_url, settings.jira_base_url, settings.jira_email, settings.jira_api_token)):
        raise RuntimeError(
            "DATABASE_URL, JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN are required."
        )
    project_keys = [key.strip() for key in settings.jira_project_keys.split(",") if key.strip()]
    if not project_keys:
        raise RuntimeError("JIRA_PROJECT_KEYS must contain at least one project key.")

    engine = create_engine_from_url(settings.database_url)
    client = JiraClient(
        settings.jira_email,
        settings.jira_api_token,
        settings.jira_base_url,
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
            synchronized = run_with_retries(
                session,
                organization,
                "jira",
                lambda: JiraSyncService().sync(session, organization, client, project_keys),
            )
            print(f"Synchronized {synchronized} Jira records.")
    finally:
        client.close()
        engine.dispose()


if __name__ == "__main__":
    main()
