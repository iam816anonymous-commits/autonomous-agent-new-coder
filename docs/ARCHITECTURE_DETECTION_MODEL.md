# Architecture Detection Model

## 1. Boundary Pattern Detection
`ArchitectureDetector` scans source file paths and package structures to detect architectural patterns:
* `SERVICE_REPOSITORY` (`controllers/`, `services/`, `repositories/`)
* `LAYERED`
* `API_CONTROLLER` (`routes/`, `api/`)
* `MVC`

Returns evidence and confidence bounds (`HIGH`, `MEDIUM`, `UNKNOWN`).
