# Prompt Library

## Daily Summary

Summarize engineering activity and risks.

### Summary v1

Summarize the highest delivery risks from the supplied normalized risk
assessments. Keep the summary concise, identify the most important risks, and
recommend concrete next actions. Do not invent facts. Return JSON with:

```json
{
  "summary": "string",
  "risks": ["string"],
  "recommendations": ["string"],
  "confidence": 0.0
}
```

## PR Review

Review complexity, testing, security and architecture.

## Sprint Health

Assess progress and spillover risk.
