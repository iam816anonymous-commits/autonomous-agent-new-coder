"""
Typed exceptions for semantic repository intelligence.
"""

class SemanticError(Exception):
    """Base exception for all semantic repository intelligence errors."""
    pass

class SymbolResolutionError(SemanticError):
    """Raised when a symbol cannot be resolved or is missing."""
    pass

class AmbiguousSymbolError(SemanticError):
    """Raised when multiple symbol candidates match a query without a unique target."""
    pass
