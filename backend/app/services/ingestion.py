from collections.abc import Callable
from datetime import UTC, datetime
from time import sleep
from typing import TypeVar

import httpx
from sqlalchemy.orm import Session

from app.models import IngestionRun, Organization

T = TypeVar("T")


class ProviderError(RuntimeError):
    """Provider failure classified for retry orchestration."""

    retryable = False


class RetryableProviderError(ProviderError):
    """Provider failure that is safe to retry."""

    retryable = True


def run_with_retries(
    session: Session,
    organization: Organization,
    provider: str,
    operation: Callable[[], int],
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 0.1,
) -> int:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    run = IngestionRun(
        organization_id=organization.id,
        provider=provider,
        status="running",
        attempt_count=0,
        started_at=datetime.now(UTC),
        records_synchronized=0,
    )
    session.add(run)
    session.commit()

    for attempt in range(1, max_attempts + 1):
        run.attempt_count = attempt
        session.commit()
        try:
            synchronized = operation()
        except ProviderError as error:
            session.rollback()
            run = session.get(IngestionRun, run.id)
            if not error.retryable or attempt == max_attempts:
                _finish_failed_run(run, error)
                session.commit()
                raise
            if backoff_seconds:
                sleep(backoff_seconds * attempt)
        except httpx.TransportError as error:
            session.rollback()
            run = session.get(IngestionRun, run.id)
            if attempt == max_attempts:
                _finish_failed_run(run, error)
                session.commit()
                raise
            if backoff_seconds:
                sleep(backoff_seconds * attempt)
        except Exception as error:
            session.rollback()
            run = session.get(IngestionRun, run.id)
            _finish_failed_run(run, error)
            session.commit()
            raise
        else:
            run = session.get(IngestionRun, run.id)
            run.status = "succeeded"
            run.finished_at = datetime.now(UTC)
            run.records_synchronized = synchronized
            session.commit()
            return synchronized

    raise RuntimeError("Ingestion retry loop exited unexpectedly.")


def _finish_failed_run(run: IngestionRun, error: Exception) -> None:
    run.status = "failed"
    run.finished_at = datetime.now(UTC)
    run.error_message = str(error)[:500]
