# Production Deployment and Operations

## Overview

The Engineering Intelligence Platform requires three persistent services for production:
1. **Backend API** (`backend`) — HTTP API, dashboard aggregation, and health endpoints
2. **Background Worker** (`backend-worker`) — RQ-based job processing for GitHub/Jira ingestion
3. **Scheduler** (`backend-scheduler`) — Periodic job enqueuing at configured intervals

All three services share PostgreSQL and Redis from the platform-managed infrastructure. The application Compose file (`docker-compose.yml`) defines only these application-owned services.

## Worker Scaling

### Horizontal Scaling

RQ workers are stateless and independently consume jobs from a single Redis queue. Increase worker count by adding more `backend-worker` service replicas:

**Docker Compose (Development):**
```yaml
services:
  backend-worker:
    # ... existing config ...
    deploy:
      replicas: 3  # Increase for production
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 60s
```

**Kubernetes (Future):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-worker
spec:
  replicas: 3  # or use HorizontalPodAutoscaler
  template:
    spec:
      containers:
      - name: worker
        image: engineering-intelligence-backend:prod
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
```

### Queue Monitoring

Observe queue depth and worker load:

```bash
# Connect to Redis and inspect queue
redis-cli -u $REDIS_URL

# List all jobs in queue
ZRANGE engineering-intelligence-ingestion:jobs 0 -1

# Check job counts
HGETALL engineering-intelligence-ingestion:started_job_registry

# Monitor for job failures
HGETALL engineering-intelligence-ingestion:failed_job_registry
```

For production, integrate with RQ's built-in monitoring or use external tools:
- **RQ Dashboard** — web UI for queue inspection
- **Prometheus exporter** — metrics for Grafana
- **Custom CloudWatch/Datadog integration** — log job success/failure

## Restart Policies

### Recommended Configuration

**Development** — `restart: unless-stopped` (manual control via `docker-compose stop`)

**Production** — `restart: on-failure` with bounded retry:
```yaml
restart_policy:
  condition: on-failure
  delay: 5s
  max_attempts: 3
  window: 60s
```

This ensures transient failures (e.g., brief Redis unavailability) trigger restart attempts without infinite loops on persistent misconfigurations.

### Verification Steps

1. **Verify restart behavior after a transient failure:**
   ```bash
   # Kill a worker to simulate a crash
   docker kill <container-id>
   
   # Verify it restarts within 5 seconds
   docker ps | grep backend-worker
   ```

2. **Verify graceful shutdown and job handoff:**
   ```bash
   # Stop a worker and monitor for in-flight job completion
   docker stop --time=30 <worker-container-id>
   
   # Check Redis for jobs moved to failed registry after timeout
   redis-cli -u $REDIS_URL HGETALL engineering-intelligence-ingestion:failed_job_registry
   ```

3. **Verify no duplicate execution after restart:**
   - Confirm `IngestionRun` records show single attempt for each scheduler interval
   - Check for overlapping provider locks in Redis:
     ```bash
     redis-cli -u $REDIS_URL KEYS "engineering-intelligence-ingestion:active:*"
     ```

## Deployment Verification Checklist

Before deploying to production:

- [ ] **Redis persistence** — Enable AOF (Append-Only File) or RDB snapshots for durability
- [ ] **PostgreSQL backups** — Schedule daily automated backups with point-in-time recovery
- [ ] **Health endpoint coverage** — Verify `/health`, `/health/redis` respond within SLA
- [ ] **Logging aggregation** — Configure JSON/structured logging to a central system (CloudWatch, ELK, Datadog)
- [ ] **Metrics collection** — Export Prometheus metrics or CloudWatch metrics for CPU, memory, queue depth, job duration
- [ ] **Alerting rules** — Set alerts for:
  - API response time > 5 seconds
  - Worker queue depth > 100 jobs
  - Failed ingestion run rate > 10% over 1 hour
  - Redis connection timeouts
  - PostgreSQL connection pool exhaustion
- [ ] **Rate limiting** — Configure API rate limits per IP or authenticated user
- [ ] **Secret management** — Use platform secret store (Vault, AWS Secrets Manager, or equivalent) instead of `.env` files
- [ ] **Load balancing** — Deploy API behind a load balancer with health checks and connection pooling
- [ ] **Database connection pooling** — Use PgBouncer or equivalent; default PostgreSQL max 100 connections is insufficient for multiple replicas
- [ ] **Redis connection pooling** — Verify Redis max clients setting (default 10,000 is adequate for typical deployments)

## Monitoring and Alerting

### Key Metrics to Track

| Metric | Target | Alert If | Description |
|--------|--------|----------|-------------|
| API response time (p99) | < 2s | > 5s | Dashboard overview and risk aggregation latency |
| Worker queue depth | < 5 jobs | > 100 jobs | Backpressure on ingestion capacity |
| Ingestion run success rate | > 95% | < 90% | Provider integration health |
| Redis latency | < 10ms | > 50ms | Queue and lock performance |
| PostgreSQL connection wait time | < 100ms | > 500ms | Database pool saturation |
| Worker CPU usage | < 30% | > 80% | Resource bottleneck |
| Worker memory usage | < 256Mi | > 512Mi | Memory leak or queue explosion |
| Disk usage (PostgreSQL) | < 80% | > 90% | Backup/cleanup urgency |

### Structured Logging

All services write JSON logs to stdout. Configure collection:

```json
{
  "timestamp": "2026-08-18T14:59:23.919+05:30",
  "level": "INFO",
  "logger": "app.api.dashboard",
  "message": "GET /dashboard/overview completed",
  "organization_id": "org-001",
  "request_duration_ms": 145,
  "status_code": 200
}
```

**Collection examples:**
- **CloudWatch** — Use log group `/aws/ecs/engineering-intelligence` with JSON parsing
- **ELK** — Filebeat ships logs to Logstash; Kibana visualizes with filters by organization and status
- **Datadog** — JSON attributes are automatically extracted; build dashboards by status and latency percentiles

### External Monitoring Endpoints

| Endpoint | Frequency | Purpose |
|----------|-----------|---------|
| `GET /health` | 10s (healthcheck) | Container/process liveness; used by orchestrators |
| `GET /health/redis` | 60s (custom probe) | Redis connectivity; early warning for queue unavailability |
| `/metrics` (future) | 30s (Prometheus scrape) | CPU, memory, request counts, queue depth, job duration |

## Scaling Decisions

### When to Scale API

- Dashboard aggregation (risk scoring, overview) takes > 1s
- API request queue builds up (requests waiting in kernel buffer)
- CPU is consistently > 70%

**Action:** Add a second API instance behind a load balancer.

### When to Scale Workers

- Queue depth grows beyond 50 jobs
- Ingestion jobs wait > 30 minutes for execution
- P99 ingestion run duration > 15 minutes (suggests rate-limited providers)

**Action:** Add 1–2 worker replicas per provider. GitHub and Jira ingestions run in parallel if locks allow.

### When to Scale Redis

- Redis latency consistently > 100ms
- Redis CPU > 80%
- Network bandwidth to Redis is saturated

**Action:** Use Redis Cluster or Sentinel for replication. Verify application supports RQ + Sentinel coordination.

### When to Scale PostgreSQL

- Connection pool (default 20 per process) is regularly exhausted
- Query plan cache hit rate < 90%
- Lock wait times consistently > 1s

**Action:** 
- Increase pool size only if you've scaled API/worker replicas beyond 5 each
- Use read replicas for read-heavy workloads (dashboard overview aggregation)
- Partition ingestion history by organization and time for archive/purge

## Disaster Recovery

### Backup and Restore

**PostgreSQL:**
```bash
# Daily automated backup to S3
pg_dump -U $DB_USER $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz
aws s3 cp backup-$(date +%Y%m%d).sql.gz s3://engineering-intelligence-backups/

# Restore from backup
aws s3 cp s3://engineering-intelligence-backups/backup-20260818.sql.gz - | gunzip | psql -U $DB_USER $DATABASE_URL
```

**Redis:**
- Use AOF (Append-Only File) with fsync: everysec
- Replicate to a standby via Redis Replication or Sentinel
- Backup RDB snapshots daily to S3

**Ingestion State Recovery:**
- `IngestionRun` records retain history; no data loss on worker restart
- Provider locks expire after `INGESTION_LOCK_SECONDS` (default 7200s / 2h)
- Re-enqueue failed jobs manually via CLI or web UI

### Failover Procedure

1. **API instance failure** → Load balancer routes to healthy instance; no data loss
2. **Worker failure** → RQ moves in-flight job to failed queue; job can be retried manually or via automatic policy
3. **Redis failure** → Scheduler and worker pause (queue unavailable); jobs are not lost if Redis has AOF enabled
4. **PostgreSQL failure** → Dashboard returns `500 Internal Server Error`; restore from backup and restart services

## Configuration Reference

### Environment Variables

| Variable | Default | Purpose | Production Override |
|----------|---------|---------|----------------------|
| `ENVIRONMENT` | `development` | Feature flags and logging detail | `production` |
| `LOG_LEVEL` | `INFO` | Minimum log severity | `WARNING` (reduce noise) |
| `INGESTION_LOCK_SECONDS` | `7200` | Provider lock TTL | `3600` (1 hour) for faster recovery |
| `INGESTION_SCHEDULE_SECONDS` | `3600` | Scheduler interval | `1800` (30 min) for more frequent updates |
| `INGESTION_QUEUE_NAME` | `engineering-intelligence-ingestion` | Redis queue identifier | Same (do not change) |
| `DATABASE_SCHEMA` | `public` | PostgreSQL schema | Keep as `public` until platform migration |
| `DEFAULT_ORGANIZATION_NAME` | `Engineering Intelligence Demo` | Fallback organization | Actual organization name |
| `BACKEND_API_BASE_URL` | (from frontend `.env`) | Frontend → Backend proxy URL | Use DNS name, not IP |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | CORS allowed origin | Production frontend domain |

### Resource Limits (Recommended)

| Service | CPU | Memory | Disk | Rationale |
|---------|-----|--------|------|-----------|
| backend | 1 vCPU | 512 Mi | N/A | Dashboard aggregation and risk scoring |
| backend-worker | 0.5 vCPU per replica | 256 Mi per replica | N/A | GitHub/Jira sync with buffering |
| backend-scheduler | 0.1 vCPU | 128 Mi | N/A | Lightweight cron-like process |
| PostgreSQL (platform) | 2 vCPUs | 4 Gi | 100 Gi | Shared; adjust for other workloads |
| Redis (platform) | 1 vCPU | 2 Gi | 20 Gi | Shared; AOF + RDB snapshots |

## Security Hardening

- [ ] Rotate `GITHUB_TOKEN`, `JIRA_API_TOKEN`, `LLM_API_KEY` every 90 days
- [ ] Use a secrets store (not `.env` files) for all credentials
- [ ] Enable PostgreSQL SSL/TLS encryption in transit
- [ ] Enable Redis TLS and require password authentication
- [ ] Restrict API CORS to specific frontend domain(s)
- [ ] Use network ACLs to allow ingestion services access only to GitHub, Jira, and LiteLLM APIs
- [ ] Set database connection timeouts to prevent hung connections
- [ ] Enable PostgreSQL audit logging for sensitive tables

## Troubleshooting

### Worker not processing jobs

**Symptoms:** Queue depth growing, no ingestion runs completing.

**Diagnosis:**
```bash
# Check if worker is running
docker ps | grep backend-worker

# Check logs for errors
docker logs <worker-container> | tail -50

# Verify Redis connectivity
docker exec <worker-container> python -c "from app.queue import get_redis_connection; get_redis_connection().ping()"

# Check for stuck locks
redis-cli -u $REDIS_URL KEYS "*:active:*"
```

**Resolution:** Restart worker, delete stuck lock if lock TTL expired, verify provider credentials.

### API timeout on dashboard overview

**Symptoms:** GET /dashboard/overview takes > 10s or returns `504 Gateway Timeout`.

**Diagnosis:**
```bash
# Check database performance
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM epics WHERE organization_id = 'org-001' LIMIT 10;"

# Check for long-running queries
SELECT pid, query, query_start, state FROM pg_stat_activity WHERE query NOT LIKE '%pg_stat_activity%' ORDER BY query_start;
```

**Resolution:** Add database indexes on `organization_id`, cache popular dashboard queries, or optimize risk-scoring algorithm.

### Ingestion runs failing intermittently

**Symptoms:** Provider failures every few runs, no pattern.

**Diagnosis:**
```bash
# Check ingestion run history
psql $DATABASE_URL -c "SELECT provider, status, COUNT(*) FROM ingestion_runs GROUP BY provider, status ORDER BY status;"

# Look at error logs
docker logs <backend-container> | grep ERROR | grep -i ingestion

# Verify provider API availability
curl -i https://api.github.com/rate_limit  # GitHub rate limits
curl -i https://$JIRA_BASE_URL/rest/api/3/myself  # Jira auth
```

**Resolution:** Check provider rate limits, verify credentials have not expired, increase retry attempts, add exponential backoff.

## Performance Tuning

### PostgreSQL Optimization

```sql
-- Add indexes on frequently filtered columns
CREATE INDEX idx_epics_org_risk ON epics(organization_id, risk) WHERE status = 'open';
CREATE INDEX idx_ingestion_runs_org_provider ON ingestion_runs(organization_id, provider, created_at);

-- Enable connection pooling via PgBouncer
-- Adjust shared_buffers: set to 25% of available RAM (e.g., 1 GB on 4 GB system)
-- Adjust work_mem: set to (available_RAM / max_connections) / 2
-- Adjust maintenance_work_mem: set to 256 MB or higher for VACUUM

-- Monitor slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();
```

### Redis Optimization

```bash
# Tune TCP backlog for high throughput
redis-cli CONFIG SET tcp-backlog 1024

# Tune client timeouts to prevent hung connections
redis-cli CONFIG SET timeout 300

# Monitor memory fragmentation
redis-cli INFO memory | grep fragmentation
```

### Application Tuning

- Increase `INGESTION_SCHEDULE_SECONDS` to reduce lock contention if workers are CPU-bound
- Decrease `INGESTION_LOCK_SECONDS` if you want faster recovery from worker crashes
- Add `maxDOC_LIMIT` on paginated endpoints to prevent memory exhaustion

## References

- [RQ Documentation](https://python-rq.org/)
- [Redis Cluster Tutorial](https://redis.io/docs/management/replication/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/runtime-config.html)
- [Docker Compose Deploy](https://docs.docker.com/compose/compose-file/deploy/)
- [Kubernetes Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
