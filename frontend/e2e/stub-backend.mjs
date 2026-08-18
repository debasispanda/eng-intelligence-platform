import { createServer } from "node:http";

const [, , mode, portValue] = process.argv;
const port = Number(portValue);

const overview = {
  appTitle: "Engineering Intelligence",
  profile: {
    name: "Riley Chen",
    role: "VP Engineering",
    email: "riley.chen@example.com",
    avatarInitials: "RC",
  },
  kpis: [
    { title: "Open PRs", value: "38", delta: "+6 this week", trend: "up" },
  ],
  releases: [
    {
      name: "Platform 2.8",
      owner: "Core Services",
      status: "On Track",
      completion: 74,
      date: "2026-08-04",
    },
  ],
  offTimelineEpics: [],
  hotRepositories: {
    mostActive: [
      { repository: "frontend-app", metric: 36, label: "PRs this week" },
    ],
    mostFailed: [],
  },
};

createServer((request, response) => {
  if (request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ok" }));
    return;
  }

  if (request.url === "/dashboard/overview" && mode === "live") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify(overview));
    return;
  }

  if (request.url === "/dashboard/risks" && mode === "live") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(
      JSON.stringify([
        {
          entityType: "epic",
          entityId: "epic-1",
          title: "Tenant Isolation Upgrade",
          risk: "High",
          score: 85,
          confidence: 0.95,
          ruleVersion: "risk-v2",
          factors: ["Source risk is High."],
        },
      ]),
    );
    return;
  }

  response.writeHead(503, { "content-type": "application/json" });
  response.end(JSON.stringify({ detail: "Dashboard overview is unavailable." }));
}).listen(port, "127.0.0.1");
