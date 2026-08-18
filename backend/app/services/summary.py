import json
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.dashboard import RiskAssessment, SummaryResponse
from app.services.risk import RiskScoringService

SUMMARY_PROMPT_VERSION = "summary-v1"


class SummaryServiceError(RuntimeError):
    """Raised when the summary gateway cannot return valid structured output."""


class LiteLLMGateway:
    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not settings.llm_gateway_url:
            raise SummaryServiceError("LLM gateway is not configured.")
        self._client = http_client or httpx.Client(timeout=settings.llm_timeout_seconds)
        self._owns_client = http_client is None
        self._url = f"{settings.llm_gateway_url.rstrip('/')}/v1/chat/completions"
        self._model = settings.llm_model
        self._headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if settings.llm_api_key:
            self._headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def summarize(self, assessments: list[RiskAssessment]) -> SummaryResponse:
        try:
            response = self._client.post(
                self._url,
                headers=self._headers,
                json={
                    "model": self._model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Return only valid JSON with keys summary, risks, "
                                "recommendations, and confidence."
                            ),
                        },
                        {
                            "role": "user",
                            "content": _summary_prompt(assessments),
                        },
                    ],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
            )
        except httpx.RequestError as error:
            raise SummaryServiceError("LLM gateway request failed.") from error
        if response.status_code >= 400:
            raise SummaryServiceError("LLM gateway request failed.")
        try:
            content = response.json()["choices"][0]["message"]["content"]
            payload: dict[str, Any] = json.loads(content)
            return SummaryResponse(
                summary=payload["summary"],
                risks=payload["risks"],
                recommendations=payload["recommendations"],
                confidence=payload["confidence"],
                model=self._model,
                prompt_version=SUMMARY_PROMPT_VERSION,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise SummaryServiceError("LLM gateway returned invalid summary output.") from error


def get_summary(
    session: Session,
    organization_id: UUID,
    settings: Settings,
    *,
    gateway: LiteLLMGateway | None = None,
) -> SummaryResponse:
    assessments = RiskScoringService().assess(session, organization_id)
    client = gateway or LiteLLMGateway(settings)
    try:
        return client.summarize(assessments)
    finally:
        if gateway is None:
            client.close()


def _summary_prompt(assessments: list[RiskAssessment]) -> str:
    facts = [
        {
            "title": assessment.title,
            "entity_type": assessment.entity_type,
            "risk": assessment.risk,
            "score": assessment.score,
            "factors": assessment.factors,
        }
        for assessment in assessments[:10]
    ]
    return (
        "Summarize the highest delivery risks. Keep summary concise. "
        "Recommend concrete next actions. Do not invent facts.\n"
        f"Risk assessments:\n{json.dumps(facts)}"
    )
