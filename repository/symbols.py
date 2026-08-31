import ast
import os
import re
from typing import List, Dict, Set, Optional
from .models import Symbol, SymbolReference, SymbolType

class SymbolIndexer:
    """
    Indexes definitions, calls, imports, and references for Python and JS/TS source files.
    """
    def __init__(self, root: str):
        self.root = os.path.realpath(os.path.abspath(root))
        self.symbols: List[Symbol] = []
        self.references: List[SymbolReference] = []
        self.calls: Dict[str, Set[str]] = {} # caller_container -> set of callee names
        self.file_symbols: Dict[str, List[Symbol]] = {}

    def index_repository(self, file_paths: List[str]):
        """Walks provided file paths and builds symbol indexes."""
        self.symbols.clear()
        self.references.clear()
        self.calls.clear()
        self.file_symbols.clear()

        for rel_path in file_paths:
            full_path = os.path.join(self.root, rel_path)
            if not os.path.exists(full_path):
                continue

            if rel_path.endswith('.py'):
                self._index_python_file(rel_path, full_path)
            elif rel_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                self._index_jsts_file(rel_path, full_path)

    def _index_python_file(self, rel_path: str, full_path: str):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return

        symbols_in_this_file: List[Symbol] = []
        container_stack: List[str] = ["global"]

        class PythonASTVisitor(ast.NodeVisitor):
            def __init__(visitor_self):
                pass

            def visit_FunctionDef(visitor_self, node: ast.FunctionDef):
                current_container = container_stack[-1]
                sym_type = SymbolType.METHOD if current_container != "global" and not current_container.startswith("func:") else SymbolType.FUNCTION
                sym = Symbol(
                    name=node.name,
                    symbol_type=sym_type,
                    file_path=rel_path,
                    line=node.lineno,
                    column=node.col_offset,
                    container=current_container
                )
                self.symbols.append(sym)
                symbols_in_this_file.append(sym)

                container_stack.append(f"{rel_path}:{node.name}")
                visitor_self.generic_visit(node)
                container_stack.pop()

            def visit_AsyncFunctionDef(visitor_self, node: ast.AsyncFunctionDef):
                current_container = container_stack[-1]
                sym_type = SymbolType.METHOD if current_container != "global" and not current_container.startswith("func:") else SymbolType.ASYNC_FUNCTION
                sym = Symbol(
                    name=node.name,
                    symbol_type=sym_type,
                    file_path=rel_path,
                    line=node.lineno,
                    column=node.col_offset,
                    container=current_container
                )
                self.symbols.append(sym)
                symbols_in_this_file.append(sym)

                container_stack.append(f"{rel_path}:{node.name}")
                visitor_self.generic_visit(node)
                container_stack.pop()

            def visit_ClassDef(visitor_self, node: ast.ClassDef):
                current_container = container_stack[-1]
                sym = Symbol(
                    name=node.name,
                    symbol_type=SymbolType.CLASS,
                    file_path=rel_path,
                    line=node.lineno,
                    column=node.col_offset,
                    container=current_container
                )
                self.symbols.append(sym)
                symbols_in_this_file.append(sym)

                container_stack.append(f"{rel_path}:{node.name}")
                visitor_self.generic_visit(node)
                container_stack.pop()

            def visit_Import(visitor_self, node: ast.Import):
                current_container = container_stack[-1]
                for alias in node.names:
                    sym = Symbol(
                        name=alias.asname or alias.name,
                        symbol_type=SymbolType.IMPORT,
                        file_path=rel_path,
                        line=node.lineno,
                        column=node.col_offset,
                        container=current_container
                    )
                    self.symbols.append(sym)
                    symbols_in_this_file.append(sym)

            def visit_ImportFrom(visitor_self, node: ast.ImportFrom):
                current_container = container_stack[-1]
                mod = node.module or ""
                for alias in node.names:
                    name = alias.asname or alias.name
                    sym = Symbol(
                        name=f"{mod}.{name}" if mod else name,
                        symbol_type=SymbolType.IMPORT,
                        file_path=rel_path,
                        line=node.lineno,
                        column=node.col_offset,
                        container=current_container
                    )
                    self.symbols.append(sym)
                    symbols_in_this_file.append(sym)

            def visit_Call(visitor_self, node: ast.Call):
                current_container = container_stack[-1]
                callee_name = None
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr

                if callee_name:
                    ref = SymbolReference(
                        symbol_name=callee_name,
                        file_path=rel_path,
                        line=node.lineno,
                        column=node.col_offset,
                        container=current_container
                    )
                    self.references.append(ref)

                    if current_container not in self.calls:
                        self.calls[current_container] = set()
                    self.calls[current_container].add(callee_name)

                visitor_self.generic_visit(node)

            def visit_Name(visitor_self, node: ast.Name):
                if isinstance(node.ctx, ast.Load):
                    current_container = container_stack[-1]
                    ref = SymbolReference(
                        symbol_name=node.id,
                        file_path=rel_path,
                        line=node.lineno,
                        column=node.col_offset,
                        container=current_container
                    )
                    self.references.append(ref)

        visitor = PythonASTVisitor()
        visitor.visit(tree)
        self.file_symbols[rel_path] = symbols_in_this_file

    def _index_jsts_file(self, rel_path: str, full_path: str):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return

        symbols_in_this_file: List[Symbol] = []

        # Regex pattern matchers for JS/TS declarations
        func_pattern = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)')
        arrow_pattern = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>')
        class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)')
        import_pattern = re.compile(r'^\s*import\s+(?:\{([^}]+)\}|([a-zA-Z0-9_$]+))\s+from')
        call_pattern = re.compile(r'\b([a-zA-Z0-9_$]+)\s*\(')

        for line_idx, line in enumerate(lines, start=1):
            # Function
            m_func = func_pattern.search(line)
            if m_func:
                sym = Symbol(
                    name=m_func.group(1),
                    symbol_type=SymbolType.FUNCTION,
                    file_path=rel_path,
                    line=line_idx,
                    column=m_func.start(1)
                )
                self.symbols.append(sym)
                symbols_in_this_file.append(sym)
                continue

            # Arrow Function
            m_arrow = arrow_pattern.search(line)
            if m_arrow:
                sym = Symbol(
                    name=m_arrow.group(1),
                    symbol_type=SymbolType.FUNCTION,
                    file_path=rel_path,
                    line=line_idx,
                    column=m_arrow.start(1)
                )
                self.symbols.append(sym)
                symbols_in_this_file.append(sym)
                continue

            # Class
            m_class = class_pattern.search(line)
            if m_class:
                sym = Symbol(
                    name=m_class.group(1),
                    symbol_type=SymbolType.CLASS,
                    file_path=rel_path,
                    line=line_idx,
                    column=m_class.start(1)
                )
                self.symbols.append(sym)
                symbols_in_this_file.append(sym)
                continue

            # Import
            m_imp = import_pattern.search(line)
            if m_imp:
                named = m_imp.group(1)
                default_imp = m_imp.group(2)
                imp_names = []
                if named:
                    imp_names.extend([n.strip().split(' as ')[-1] for n in named.split(',')])
                if default_imp:
                    imp_names.append(default_imp.strip())

                for name in imp_names:
                    if name:
                        sym = Symbol(
                            name=name,
                            symbol_type=SymbolType.IMPORT,
                            file_path=rel_path,
                            line=line_idx,
                            column=m_imp.start()
                        )
                        self.symbols.append(sym)
                        symbols_in_this_file.append(sym)

            # Function calls
            for m_call in call_pattern.finditer(line):
                callee_name = m_call.group(1)
                if callee_name not in {"if", "for", "while", "switch", "catch", "function", "import", "require"}:
                    ref = SymbolReference(
                        symbol_name=callee_name,
                        file_path=rel_path,
                        line=line_idx,
                        column=m_call.start(1),
                        container=rel_path
                    )
                    self.references.append(ref)

        self.file_symbols[rel_path] = symbols_in_this_file

    def find_symbol(self, name: str) -> List[Symbol]:
        return [s for s in self.symbols if s.name == name]

    def find_definitions(self, name: str) -> List[Symbol]:
        return [s for s in self.symbols if s.name == name and s.symbol_type != SymbolType.IMPORT]

    def find_references(self, name: str) -> List[SymbolReference]:
        return [r for r in self.references if r.symbol_name == name]

    def get_callers(self, symbol_name: str) -> List[str]:
        """Returns list of containers/files that call symbol_name."""
        callers = set()
        for container, callees in self.calls.items():
            if symbol_name in callees:
                callers.add(container.split(':')[0])
        for ref in self.references:
            if ref.symbol_name == symbol_name:
                callers.add(ref.file_path)
        return sorted(list(callers))

    def get_callees(self, container_or_symbol: str) -> List[str]:
        """Returns list of callees called inside container_or_symbol."""
        callees = set()
        for container, c_set in self.calls.items():
            if container == container_or_symbol or container.endswith(f":{container_or_symbol}"):
                callees.update(c_set)
        return sorted(list(callees))

    def get_symbols_in_file(self, path: str) -> List[Symbol]:
        return self.file_symbols.get(path, [s for s in self.symbols if s.file_path == path])
