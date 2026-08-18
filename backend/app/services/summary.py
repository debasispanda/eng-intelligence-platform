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
        request = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only JSON. Keys must be summary (string), risks "
                        "(array of strings), recommendations (array of strings), "
                        "and confidence (number from 0 to 1)."
                    ),
                },
                {
                    "role": "user",
                    "content": _summary_prompt(assessments),
                },
            ],
            "temperature": 0,
            "max_tokens": 600,
            "response_format": {"type": "json_object"},
        }
        last_error: SummaryServiceError | None = None
        for attempt in range(2):
            try:
                response = self._client.post(
                    self._url,
                    headers=self._headers,
                    json=request,
                )
                if response.status_code >= 400:
                    raise SummaryServiceError("LLM gateway request failed.")
                return self._parse_response(response)
            except httpx.RequestError as error:
                last_error = SummaryServiceError("LLM gateway request failed.")
                last_error.__cause__ = error
            except SummaryServiceError as error:
                last_error = error
            if attempt == 1:
                raise last_error
        raise last_error or SummaryServiceError("LLM gateway request failed.")

    def _parse_response(self, response: httpx.Response) -> SummaryResponse:
        try:
            content = response.json()["choices"][0]["message"]["content"]
            payload: dict[str, Any] = json.loads(content)
            return SummaryResponse(
                summary=payload["summary"],
                risks=_parse_items(payload["risks"]),
                recommendations=_parse_items(payload["recommendations"]),
                confidence=_parse_confidence(payload["confidence"]),
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


def _parse_confidence(value: Any) -> float:
    if isinstance(value, bool):
        raise TypeError("Confidence must be numeric.")
    if isinstance(value, (int, float)):
        confidence = float(value)
        return confidence / 100 if confidence > 1 else confidence
    if isinstance(value, str):
        label = value.strip().lower()
        if label.startswith("high"):
            return 0.9
        if label.startswith("medium"):
            return 0.6
        if label.startswith("low"):
            return 0.3
        return float(label)
    raise TypeError("Confidence must be numeric.")


def _parse_items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise TypeError("Summary items must be strings or lists of strings.")
