from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .models import SandboxSpec, SandboxResult, ExecutionCapability, SandboxMode, SandboxStatus

class SandboxBackend(ABC):
    """
    Abstract interface for all sandbox execution backends.
    """
    def __init__(self, spec: SandboxSpec):
        self.spec = spec
        self.status = SandboxStatus.CREATED

    @abstractmethod
    def create(self) -> None:
        """Initializes sandbox structures and resources."""
        pass

    @abstractmethod
    def prepare(self) -> None:
        """Prepares workspace environment prior to execution."""
        pass

    @abstractmethod
    def execute(self, command_name: str, args: List[str], env: Optional[Dict[str, str]] = None) -> SandboxResult:
        """Executes a command within the sandbox boundaries."""
        pass

    @abstractmethod
    def terminate(self) -> None:
        """Terminates any running sandbox processes or resources."""
        pass

    @abstractmethod
    def cleanup(self) -> Dict[str, Any]:
        """Cleans up sandbox artifacts and returns cleanup status."""
        pass

    @abstractmethod
    def supports_capability(self, capability: ExecutionCapability) -> bool:
        """Checks if backend supports the requested capability."""
        pass

    @abstractmethod
    def enforcement_status(self) -> Dict[str, Any]:
        """Reports metadata on active, enforced, and unenforced security limitations."""
        pass
