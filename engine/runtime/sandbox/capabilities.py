from typing import Set, Iterable
from .models import ExecutionCapability
from .errors import CapabilityViolationError

class CapabilitySet:
    """
    Enforces deny-by-default capability boundaries and escalation checks.
    """
    def __init__(self, capabilities: Iterable[ExecutionCapability] = ()):
        self._capabilities: Set[ExecutionCapability] = set(capabilities)

    @property
    def capabilities(self) -> Set[ExecutionCapability]:
        return set(self._capabilities)

    def has(self, capability: ExecutionCapability) -> bool:
        if not isinstance(capability, ExecutionCapability):
            return False
        return capability in self._capabilities

    def require(self, capability: ExecutionCapability) -> None:
        if not self.has(capability):
            raise CapabilityViolationError(
                f"Capability violation: '{capability.value}' is denied or not granted in parent policy."
            )

    def require_all(self, capabilities: Iterable[ExecutionCapability]) -> None:
        for cap in capabilities:
            self.require(cap)

    def is_subset_of(self, parent: "CapabilitySet") -> bool:
        return self._capabilities.issubset(parent._capabilities)

    def validate_child(self, child: "CapabilitySet") -> None:
        """
        Ensures child policy does not escalate capabilities beyond parent policy.
        """
        escalated = child._capabilities - self._capabilities
        if escalated:
            escaped_names = [c.value for c in escalated]
            raise CapabilityViolationError(
                f"Capability escalation rejected! Child attempted to claim ungranted capabilities: {escaped_names}"
            )
