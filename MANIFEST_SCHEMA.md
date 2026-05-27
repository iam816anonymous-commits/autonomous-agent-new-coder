# Project Manifest Schema (project.yaml)

The `project.yaml` file acts as the immutable source of truth for every Mini Jules project.

## Schema Definition

```yaml
project:
  id: string           # Unique project identifier (e.g., p_123456789)
  goal: string         # The user's original objective
  status: string       # initialized | active | validated | complete
  stack: string        # Tech stack (e.g., fastapi, nextjs)
  modules:             # Map of logical modules to files
    backend: [string]
    frontend: [string]
  files:               # Detailed file status and history
    filename:
      status: string   # pending | generated | applied
      critique_history:
        - timestamp: float
          verdict: PASS | FAIL
          issues: [string]
  patches:
    pending: [string]  # Files with unapplied repairs
    approved: [string] # Files with approved but unmerged patches
  approvals: [string]  # List of files successfully applied
  validation:
    tests: string      # pending | pass | fail
  sessions: [string]   # History of agent session IDs
```

## Usage
Mini Jules reads this manifest at startup to determine where to resume and which files require auditing or repair.
