import { dashboardData } from "@/lib/dashboard-data";
import { SectionCard } from "@/components/ui/section-card";
import { StatCard } from "@/components/ui/stat-card";
import { StatusBadge } from "@/components/ui/status-badge";

export default function Home() {
  return (
    <div className="dashboard-wrap">
      <section className="kpi-grid" aria-label="Key metrics">
        {dashboardData.kpis.map((card) => (
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
            {dashboardData.releases.map((release) => (
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
              {dashboardData.offTimelineEpics.map((epic) => (
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

      <section className="content-grid two-col">
        <SectionCard
          title="Hot Repositories: Most Active"
          description="Repositories with highest pull request activity"
        >
          <ul className="repo-list">
            {dashboardData.hotRepositories.mostActive.map((repo) => (
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
            {dashboardData.hotRepositories.mostFailed.map((repo) => (
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
