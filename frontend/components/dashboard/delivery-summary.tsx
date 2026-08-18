"use client";

import { useEffect, useState } from "react";
import { SectionCard } from "@/components/ui/section-card";
import type { DeliverySummary } from "@/lib/dashboard-types";

type DeliverySummaryPanelProps = {
  initialSummary?: DeliverySummary | null;
  initialError?: string | null;
};

export function DeliverySummaryPanel({
  initialSummary = null,
  initialError = null,
}: DeliverySummaryPanelProps) {
  const [summary, setSummary] = useState<DeliverySummary | null>(initialSummary);
  const [error, setError] = useState<string | null>(initialError);
  const [loading, setLoading] = useState(initialSummary === null && initialError === null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    if (initialSummary !== null || initialError !== null) {
      return;
    }

    let cancelled = false;
    fetch("/api/dashboard/summary", {
      headers: { Accept: "application/json" },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Delivery summary is temporarily unavailable.");
        }
        return (await response.json()) as DeliverySummary;
      })
      .then((value) => {
        if (!cancelled) {
          setSummary(value);
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Delivery summary is temporarily unavailable.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [initialError, initialSummary, retryKey]);

  return (
    <SectionCard
      title="AI Delivery Summary"
      description="Generated from the latest explainable risk assessments"
    >
      {loading ? (
        <div className="summary-loading" role="status" aria-label="Generating delivery summary">
          <span className="summary-spinner" aria-hidden="true" />
          <div>
            <strong>Generating delivery summary</strong>
            <span>Analyzing current delivery signals...</span>
          </div>
          <div className="summary-skeleton" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : error !== null ? (
        <div className="summary-error">
          <p className="muted-message">{error}</p>
          <button type="button" className="summary-retry" onClick={() => {
            setError(null);
            setLoading(true);
            setRetryKey((value) => value + 1);
          }}>
            Try again
          </button>
        </div>
      ) : summary === null ? (
        <p className="muted-message">No delivery summary available.</p>
      ) : (
        <div className="summary-content">
          <div className="summary-insight">
            <span className="summary-eyebrow">Executive readout</span>
            <p className="summary-lead"><MetricText text={summary.summary} /></p>
          </div>
          <div className="summary-columns">
            <SummaryColumn
              title="Key risks"
              items={summary.risks}
              emptyLabel="No risks identified."
              tone="negative"
            />
            <SummaryColumn
              title="Recommended actions"
              items={summary.recommendations}
              emptyLabel="No recommendations available."
              tone="positive"
            />
          </div>
          <small className="summary-meta">
            Confidence {Math.round(summary.confidence * 100)}% · {summary.model} ·{" "}
            {summary.promptVersion}
          </small>
        </div>
      )}
    </SectionCard>
  );
}

function SummaryColumn({
  title,
  items,
  emptyLabel,
  tone,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
  tone: "negative" | "positive";
}) {
  return (
    <div className={`summary-column summary-column-${tone}`}>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="muted-message">{emptyLabel}</p>
      ) : (
        <ul className="summary-list">
          {items.slice(0, 5).map((item) => (
            <li key={item}>
              {tone === "negative" ? (
                <RiskItem text={item} />
              ) : (
                <MetricText text={item} />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function RiskItem({ text }: { text: string }) {
  const separatorIndex = text.indexOf(":");
  if (separatorIndex < 0) {
    return <MetricText text={text} />;
  }

  const title = text.slice(0, separatorIndex).trim();
  const detail = text.slice(separatorIndex + 1).trim();

  return (
    <span className="summary-risk-item">
      <strong className="summary-risk-title">{title}</strong>
      <span className="summary-risk-detail">
        <MetricText text={detail} />
      </span>
    </span>
  );
}

function MetricText({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\b\d+(?:\.\d+)?%?)/g).map((part, index) =>
        /^\d/.test(part) ? (
          <strong key={`${part}-${index}`} className="summary-metric">{part}</strong>
        ) : (
          part
        ),
      )}
    </>
  );
}
