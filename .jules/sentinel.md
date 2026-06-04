# Sentinel's Journal

## 2025-05-15 - [Sandbox Constraint Hardening]
**Learning:** Subprocess execution with shell=False is a good start, but environment sanitization (PYTHONPATH, PATH) is critical to prevent privilege escalation or side-loading in sandboxed venvs.
**Action:** Strictly control environment variables passed to subprocess.run.
