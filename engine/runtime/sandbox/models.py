from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
import time

class SandboxMode(Enum):
    STATIC_ONLY = "STATIC_ONLY"
    RESTRICTED_LOCAL = "RESTRICTED_LOCAL"
    ISOLATED = "ISOLATED"

class SandboxStatus(Enum):
    CREATED = "CREATED"
    PREPARING = "PREPARING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"
    ROLLED_BACK = "ROLLED_BACK"

class FilesystemAccess(Enum):
    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    WORKSPACE_READ_WRITE = "WORKSPACE_READ_WRITE"

class NetworkAccess(Enum):
    DENY = "DENY"
    ALLOW = "ALLOW"

class ExecutionCapability(Enum):
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    READ_WORKSPACE = "READ_WORKSPACE"
    WRITE_WORKSPACE = "WRITE_WORKSPACE"
    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    RUN_TESTS = "RUN_TESTS"
    NETWORK = "NETWORK"
    INSTALL_DEPENDENCY = "INSTALL_DEPENDENCY"

class ExecutionTrustLevel(Enum):
    NO_CODE_EXECUTION = "NO_CODE_EXECUTION"
    TRUSTED_TOOL_ONLY = "TRUSTED_TOOL_ONLY"
    UNTRUSTED_REPOSITORY_CODE = "UNTRUSTED_REPOSITORY_CODE"

class TransactionPolicy(Enum):
    DISCARD_ALWAYS = "DISCARD_ALWAYS"
    COMMIT_ON_SUCCESS = "COMMIT_ON_SUCCESS"
    READ_ONLY = "READ_ONLY"

@dataclass
class ResourceLimits:
    timeout_seconds: float = 30.0
    max_output_bytes: int = 1_000_000
    max_memory_mb: Optional[int] = None
    max_cpu_cores: Optional[float] = None
    max_processes: Optional[int] = None
    enforceable_limits: List[str] = field(default_factory=lambda: ["timeout_seconds", "max_output_bytes"])

@dataclass
class SandboxSpec:
    sandbox_id: str
    mode: SandboxMode
    workspace_root: str
    filesystem_access: FilesystemAccess = FilesystemAccess.READ_ONLY
    network_access: NetworkAccess = NetworkAccess.DENY
    allowed_capabilities: Set[ExecutionCapability] = field(default_factory=set)
    trust_level: ExecutionTrustLevel = ExecutionTrustLevel.NO_CODE_EXECUTION
    timeout: float = 30.0
    stdout_byte_limit: int = 1_000_000
    stderr_byte_limit: int = 1_000_000
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    environment_policy: Dict[str, str] = field(default_factory=dict)
    transaction_policy: TransactionPolicy = TransactionPolicy.DISCARD_ALWAYS
    created_at: float = field(default_factory=time.time)

@dataclass
class ExecutionApproval:
    approval_id: str
    approved_capabilities: Set[ExecutionCapability]
    workspace_id_or_fingerprint: str
    trust_level: ExecutionTrustLevel
    issued_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def is_valid_for(self, workspace_fingerprint: str, required_trust: ExecutionTrustLevel, required_caps: Set[ExecutionCapability], now: Optional[float] = None) -> bool:
        current_time = now if now is not None else time.time()
        if self.expires_at is not None and current_time > self.expires_at:
            return False
        if self.workspace_id_or_fingerprint != workspace_fingerprint:
            return False
        # Trust level check: approval trust must be >= required trust severity
        trust_order = {
            ExecutionTrustLevel.NO_CODE_EXECUTION: 1,
            ExecutionTrustLevel.TRUSTED_TOOL_ONLY: 2,
            ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE: 3,
        }
        if trust_order.get(self.trust_level, 0) < trust_order.get(required_trust, 0):
            return False
        # Capabilities check
        if not required_caps.issubset(self.approved_capabilities):
            return False
        return True

@dataclass
class SandboxResult:
    sandbox_id: str
    status: SandboxStatus
    execution_result: Optional[Dict[str, Any]] = None
    enforcement_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    snapshot_before_hash: Optional[str] = None
    snapshot_after_hash: Optional[str] = None
    duration: float = 0.0
    cleanup_result: Dict[str, Any] = field(default_factory=dict)
