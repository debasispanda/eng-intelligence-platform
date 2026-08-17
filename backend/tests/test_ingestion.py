from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import IngestionRun, Organization
from app.services.ingestion import ProviderError, run_with_retries


def test_run_with_retries_records_success_after_transient_failure() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    attempts = 0

    with Session(engine) as session:
        organization = Organization(name="Test")
        session.add(organization)
        session.commit()

        def operation() -> int:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                error = ProviderError("temporarily unavailable")
                error.retryable = True
                raise error
            return 7

        assert run_with_retries(
            session,
            organization,
            "jira",
            operation,
            backoff_seconds=0,
        ) == 7
        run = session.scalar(select(IngestionRun))

    assert run is not None
    assert run.status == "succeeded"
    assert run.attempt_count == 2
    assert run.records_synchronized == 7


def test_run_with_retries_does_not_retry_non_retryable_provider_error() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    attempts = 0

    with Session(engine) as session:
        organization = Organization(name="Test")
        session.add(organization)
        session.commit()

        def operation() -> int:
            nonlocal attempts
            attempts += 1
            raise ProviderError("invalid credentials")

        try:
            run_with_retries(session, organization, "github", operation, backoff_seconds=0)
        except ProviderError:
            pass
        else:
            raise AssertionError("expected provider error")
        run = session.scalar(select(IngestionRun))

    assert attempts == 1
    assert run is not None
    assert run.status == "failed"
    assert run.attempt_count == 1
    assert run.error_message == "invalid credentials"
