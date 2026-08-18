"use client";

import { useDashboardData } from "@/components/dashboard/dashboard-provider";
import { SectionCard } from "@/components/ui/section-card";
import { StatCard } from "@/components/ui/stat-card";
import { StatusBadge } from "@/components/ui/status-badge";
import type {
  DashboardOverview,
  DeliverySummary,
  RiskAssessment,
} from "@/lib/dashboard-types";

export default function Home() {
  const { error, overview, riskError, risks, summary, summaryError } =
    useDashboardData();

  if (error !== null) {
    return <DashboardMessage title="Dashboard unavailable" message={error} />;
  }

  if (overview === null || isDashboardEmpty(overview)) {
    return (
      <DashboardMessage
        title="No dashboard data yet"
        message="Connect an engineering data source or seed the development database to populate this overview."
      />
    );
  }

  return (
    <DashboardContent
      overview={overview}
      riskError={riskError}
      risks={risks}
      summary={summary}
      summaryError={summaryError}
    />
  );
}

function isDashboardEmpty(overview: DashboardOverview): boolean {
  return (
    overview.kpis.length === 0 &&
    overview.releases.length === 0 &&
    overview.offTimelineEpics.length === 0 &&
    overview.hotRepositories.mostActive.length === 0 &&
    overview.hotRepositories.mostFailed.length === 0
  );
}

export function DashboardContent({
  overview,
  riskError,
  risks,
  summary,
  summaryError,
}: {
  overview: DashboardOverview;
  riskError: string | null;
  risks: RiskAssessment[];
  summary: DeliverySummary | null;
  summaryError: string | null;
}) {
  return (
    <div className="dashboard-wrap">
      <section className="kpi-grid" aria-label="Key metrics">
        {overview.kpis.map((card) => (
          <div key={card.title} className="reveal">
            <StatCard
              title={card.title}
              value={card.value}
              delta={card.delta}
              trend={card.trend}
            />
          </div>
        ))}
      </section>

      <section className="content-grid">
        <SectionCard
          title="Release Status"
          description="Current release trains and delivery confidence"
        >
          <div className="table-wrap" role="table" aria-label="Release status rows">
            <div className="table-head" role="row">
              <span role="columnheader">Release</span>
              <span role="columnheader">Owner</span>
              <span role="columnheader">Status</span>
              <span role="columnheader">Completion</span>
              <span role="columnheader">Target</span>
            </div>
            {overview.releases.map((release) => (
              <div key={release.name} className="table-row" role="row">
                <span role="cell" data-label="Release">
                  {release.name}
                </span>
                <span role="cell" data-label="Owner">
                  {release.owner}
                </span>
                <span role="cell" data-label="Status">
                  <StatusBadge value={release.status} />
                </span>
                <span role="cell" data-label="Completion">
                  {release.completion}%
                </span>
                <span role="cell" data-label="Target">
                  {release.date}
                </span>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="AI Delivery Summary"
          description="Generated from the latest explainable risk assessments"
        >
          {summaryError !== null ? (
            <p className="muted-message">{summaryError}</p>
          ) : summary === null ? (
            <p className="muted-message">No delivery summary available.</p>
          ) : (
            <div className="summary-content">
              <p className="summary-lead">{summary.summary}</p>
              <div className="summary-columns">
                <div>
                  <h3>Key risks</h3>
                  <SummaryList items={summary.risks} emptyLabel="No risks identified." />
                </div>
                <div>
                  <h3>Recommended actions</h3>
                  <SummaryList
                    items={summary.recommendations}
                    emptyLabel="No recommendations available."
                  />
                </div>
              </div>
              <small className="summary-meta">
                Confidence {Math.round(summary.confidence * 100)}% · {summary.model} ·{" "}
                {summary.promptVersion}
              </small>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Epics Off Timeline"
          description="Top epics currently running behind plan"
        >
          <table className="epics-table">
            <thead>
              <tr>
                <th>Epic</th>
                <th>Owner</th>
                <th>Delay</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {overview.offTimelineEpics.map((epic) => (
                <tr key={epic.epic}>
                  <td>{epic.epic}</td>
                  <td>{epic.owner}</td>
                  <td>{epic.delayedByDays} days</td>
                  <td>
                    <StatusBadge value={epic.risk} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>
      </section>

      <SectionCard
        title="Risk Intelligence"
        description="Explainable rule-based delivery risk assessments"
      >
        {riskError !== null ? (
          <p className="muted-message">{riskError}</p>
        ) : risks.length === 0 ? (
          <p className="muted-message">No risk assessments available.</p>
        ) : (
          <ul className="risk-list">
            {risks.slice(0, 5).map((assessment) => (
              <li key={assessment.entityId} className="risk-item">
                <div>
                  <strong>{assessment.title}</strong>
                  <span>{assessment.factors[0]}</span>
                </div>
                <StatusBadge value={assessment.risk} />
                <span className="risk-score">{assessment.score}</span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>

      <section className="content-grid two-col">
        <SectionCard
          title="Hot Repositories: Most Active"
          description="Repositories with highest pull request activity"
        >
          <ul className="repo-list">
            {overview.hotRepositories.mostActive.map((repo) => (
              <li key={repo.repository} className="repo-item">
                <span>{repo.repository}</span>
                <span>
                  {repo.metric} {repo.label}
                </span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard
          title="Hot Repositories: Most Failed"
          description="Repositories with highest build instability"
        >
          <ul className="repo-list">
            {overview.hotRepositories.mostFailed.map((repo) => (
              <li key={repo.repository} className="repo-item">
                <span>{repo.repository}</span>
                <span>
                  {repo.metric} {repo.label}
                </span>
              </li>
            ))}
          </ul>
        </SectionCard>
      </section>
    </div>
  );
}

function SummaryList({ items, emptyLabel }: { items: string[]; emptyLabel: string }) {
  if (items.length === 0) {
    return <p className="muted-message">{emptyLabel}</p>;
  }

  return (
    <ul className="summary-list">
      {items.slice(0, 5).map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function DashboardMessage({
  message,
  title,
}: {
  message: string;
  title: string;
}) {
  return (
    <section className="dashboard-message" aria-live="polite" role="status">
      <h1>{title}</h1>
      <p>{message}</p>
    </section>
  );
}
