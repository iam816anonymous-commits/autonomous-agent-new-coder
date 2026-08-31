# Workflow Lease Model

## 1. Concurrency & Ownership
* Workflows use optimistic versioning and worker lease heartbeat timestamps (`worker_id`, `lease_started_at`, `heartbeat_at`).
* Prevents two workers or processes from resuming or executing the same workflow simultaneously.
* Stale worker leases (> 60s timeout without heartbeat) are reclaimed and transitioned to `RECOVERY_REQUIRED`.
