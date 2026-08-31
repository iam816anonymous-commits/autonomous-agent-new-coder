# 🏛️ Structural Editing Architectural Decision Record (ADR)

## 1. What parser does Mini-Jules currently use?
Mini-Jules currently uses Python's standard library `ast` module and `tokenize` module for Python source files, combined with regex/pattern matching for JS/TS declarations in Phase A.

## 2. What limitations does it have?
- **Python `ast`**: Discards comments, whitespace, and formatting context during AST reconstruction, requiring python `tokenize` for token-preserving code transformations.
- **JS/TS Regex**: Pattern matching cannot reliably build full cross-file symbol call graphs for JavaScript/TypeScript or handle complex multi-file Scope resolution without full CST/AST parsing.

## 3. Where would Tree-sitter help?
Tree-sitter generates Concrete Syntax Trees (CSTs) preserving full comment, whitespace, and formatting context across multi-language codebases (Python, TypeScript, JavaScript, Go, Rust, Java, C#).

## 4. Where would ast-grep help?
ast-grep provides declarative AST search-and-replace rules powered by Tree-sitter, making multi-language structural pattern matching and refactoring concise.

## 5. Should either be added now?
**Decision**: Defer adding external C/Rust binary dependencies (Tree-sitter / ast-grep) in Phase D.1.
**Justification**: Mini-Jules prioritizes zero-dependency local execution. Python standard library `ast` + `tokenize` provides 100% exact, token-preserving Python symbol renaming without external binary dependencies. Tree-sitter/ast-grep are designated as candidate backends for future multi-language structural codemod phases.

## 6. What languages should be supported first?
1. **Python**: Primary zero-dependency standard library support (`ast` + `tokenize`).
2. **TypeScript / JavaScript**: Primary frontend language target for future Tree-sitter bindings.

## 7. What is the fallback behavior when structural support is unavailable?
If a language or file type lacks AST/tokenize structural rewriting (e.g. non-Python files), the operator flags `UNSUPPORTED_LANGUAGE_OPERATION` and skips risky textual/regex substitution to prevent code corruption.
