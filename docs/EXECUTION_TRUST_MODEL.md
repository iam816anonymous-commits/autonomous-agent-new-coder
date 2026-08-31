# Execution Trust Model

## 1. Trust Classification
Mini-Jules categorizes all operations into explicit execution trust levels to ensure human operators are fully informed before commands execute.

```text
NO_CODE_EXECUTION (Level 1)
  │  No repository code or scripts are executed.
  │  Safe for unapproved automated processing.
  ▼
TRUSTED_TOOL_ONLY (Level 2)
  │  Executes binary tools (e.g., system linter) without loading untrusted repo scripts.
  ▼
UNTRUSTED_REPOSITORY_CODE (Level 3)
     Executes project test suites (pytest, jest, python) which import and execute repository code.
     Requires explicit human execution approval (execution_approved=True).
```

---

## 2. Execution Approval Binding
`ExecutionApproval` objects are cryptographically bound to:
1. **Workspace Fingerprint**: SHA-256 summary hash of the workspace snapshot.
2. **Approved Capability Set**: Explicit list of allowed capabilities.
3. **Trust Level**: Maximum allowed execution trust level.
4. **Expiration Timestamp**: Expiration time after which approval fails closed.
