from enum import Enum


class ErrorSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ErrorCategory(Enum):
    SYNTAX = "SYNTAX"
    IMPORT = "IMPORT"
    TYPE = "TYPE"
    LOGIC = "LOGIC"
    RUNTIME = "RUNTIME"
    BUILD = "BUILD"
    CONFIG = "CONFIG"
    DEPENDENCY = "DEPENDENCY"
    API_CONTRACT = "API_CONTRACT"
    CIRCULAR_DEP = "CIRCULAR_DEP"


class ErrorClassifier:
    """
    Categorizes errors and suggests targeted repair strategies.
    """

    def classify_error(self, message):
        msg = message.lower()
        if "syntax" in msg:
            return ErrorCategory.SYNTAX, ErrorSeverity.HIGH
        if "import" in msg or "notfound" in msg:
            return ErrorCategory.IMPORT, ErrorSeverity.MEDIUM
        if "type" in msg:
            return ErrorCategory.TYPE, ErrorSeverity.MEDIUM
        if "assert" in msg:
            return ErrorCategory.LOGIC, ErrorSeverity.HIGH
        if "recursion" in msg or "circular" in msg:
            return ErrorCategory.CIRCULAR_DEP, ErrorSeverity.CRITICAL

        return ErrorCategory.RUNTIME, ErrorSeverity.MEDIUM

    def get_repair_plan(self, category):
        plans = {
            ErrorCategory.SYNTAX: "Check for missing brackets, colons, or indentation errors. Verify string termination.",
            ErrorCategory.IMPORT: "Verify file paths and module names. Ensure all files are generated before their dependents.",
            ErrorCategory.TYPE: "Verify function signatures and data structures. Check for None values.",
            ErrorCategory.LOGIC: "Check algorithm logic and edge cases. Verify unit test assertions.",
            ErrorCategory.CIRCULAR_DEP: "Refactor to move shared logic to a common 'core' or 'utils' module.",
            ErrorCategory.RUNTIME: "Examine stack trace for null pointers or resource unavailability.",
        }
        return plans.get(category, "Review the logs and perform a general repair.")

    def should_attempt_repair(self, attempt_count):
        return attempt_count < 3
