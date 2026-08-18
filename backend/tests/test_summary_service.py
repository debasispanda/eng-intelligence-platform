import httpx
import pytest

from app.core.config import Settings
from app.schemas.dashboard import RiskAssessment
from app.services.summary import (
    LiteLLMGateway,
    SummaryServiceError,
    _summary_prompt,
)


def _assessment() -> RiskAssessment:
    return RiskAssessment(
        entity_type="epic",
        entity_id="epic-1",
        title="Tenant Isolation Upgrade",
        risk="High",
        score=85,
        confidence=0.9,
        rule_version="risk-v2",
        factors=["Source risk is High."],
    )


def test_summary_gateway_validates_structured_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"summary":"Focus on the delayed epic.",'
                                '"risks":["Tenant Isolation Upgrade"],'
                                '"recommendations":["Review delivery plan."],'
                                '"confidence":0.88}'
                            )
                        }
                    }
                ]
            },
        )

    settings = Settings(
        llm_gateway_url="https://llm.example.com",
        llm_api_key="test-key",
        llm_model="test-model",
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    gateway = LiteLLMGateway(settings, http_client=client)

    result = gateway.summarize([_assessment()])

    assert result.summary == "Focus on the delayed epic."
    assert result.risks == ["Tenant Isolation Upgrade"]
    assert result.confidence == 0.88
    assert result.model == "test-model"
    assert result.prompt_version == "summary-v1"


def test_summary_gateway_rejects_invalid_response() -> None:
    settings = Settings(llm_gateway_url="https://llm.example.com")
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={"choices": [{"message": {"content": "not-json"}}]},
            )
        )
    )
    gateway = LiteLLMGateway(settings, http_client=client)

    with pytest.raises(SummaryServiceError, match="invalid summary output"):
        gateway.summarize([_assessment()])


def test_summary_gateway_normalizes_labeled_confidence() -> None:
    settings = Settings(llm_gateway_url="https://llm.example.com")
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"summary":"Summary","risks":[],"recommendations":[],'
                                    '"confidence":"low - limited evidence"}'
                                )
                            }
                        }
                    ]
                },
            )
        )
    )
    gateway = LiteLLMGateway(settings, http_client=client)

    assert gateway.summarize([]).confidence == 0.3


def test_summary_prompt_contains_only_normalized_risk_facts() -> None:
    prompt = _summary_prompt([_assessment()])

    assert "Tenant Isolation Upgrade" in prompt
    assert "risk-v2" not in prompt
    assert "Source risk is High." in prompt
