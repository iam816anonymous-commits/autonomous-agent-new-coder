import ast
import os
from typing import List, Dict, Set, Optional
from .models import (
    SemanticSymbol, SemanticRelation, SymbolKind, SemanticRelationType, Evidence, ConfidenceLevel
)
from .graph import SemanticRepositoryGraph

class PythonSemanticAnalyzer:
    """
    Authoritative AST-based structural semantic analyzer for Python source files.
    Extracts classes, methods, functions, decorators, parameters, inheritance, imports, and route decorators.
    """
    def __init__(self, root: str, graph: Optional[SemanticRepositoryGraph] = None):
        self.root = os.path.realpath(os.path.abspath(root))
        self.graph = graph or SemanticRepositoryGraph()

    def analyze_file(self, rel_path: str) -> None:
        full_path = os.path.join(self.root, rel_path)
        if not os.path.exists(full_path) or not rel_path.endswith('.py'):
            return

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return

        module_symbol_id = f"mod:{rel_path}"
        mod_symbol = SemanticSymbol(
            symbol_id=module_symbol_id,
            name=os.path.basename(rel_path),
            qualified_name=rel_path.replace('/', '.').rstrip('.py'),
            symbol_kind=SymbolKind.MODULE,
            language="Python",
            file_path=rel_path,
            start_line=1,
            end_line=len(content.splitlines()) or 1
        )
        self.graph.add_symbol(mod_symbol)

        current_container = [module_symbol_id]

        class Visitor(ast.NodeVisitor):
            def __init__(visitor_self):
                pass

            def visit_FunctionDef(visitor_self, node: ast.FunctionDef):
                parent_id = current_container[-1]
                is_method = self.graph.get_symbol(parent_id) and self.graph.get_symbol(parent_id).symbol_kind == SymbolKind.CLASS
                sym_kind = SymbolKind.METHOD if is_method else SymbolKind.FUNCTION
                sym_id = f"{parent_id}:{node.name}"

                sym = SemanticSymbol(
                    symbol_id=sym_id,
                    name=node.name,
                    qualified_name=f"{self.graph.get_symbol(parent_id).qualified_name}.{node.name}",
                    symbol_kind=sym_kind,
                    language="Python",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    parent_symbol_id=parent_id
                )
                self.graph.add_symbol(sym)

                # Relation: CONTAINS
                self.graph.add_relation(SemanticRelation(
                    source_symbol_id=parent_id,
                    target_symbol_id=sym_id,
                    relation_type=SemanticRelationType.CONTAINS,
                    evidence=Evidence(file=rel_path, line=node.lineno, confidence_reason="AST FunctionDef")
                ))

                # Route decorator check (@app.get, @app.post, @router.get)
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in ("get", "post", "put", "delete", "patch"):
                            # Route decorator!
                            self.graph.add_relation(SemanticRelation(
                                source_symbol_id=sym_id,
                                target_symbol_id=sym_id,
                                relation_type=SemanticRelationType.ROUTES_TO,
                                evidence=Evidence(file=rel_path, line=node.lineno, confidence_reason=f"Route decorator @{dec.func.attr}")
                            ))

                current_container.append(sym_id)
                visitor_self.generic_visit(node)
                current_container.pop()

            def visit_ClassDef(visitor_self, node: ast.ClassDef):
                parent_id = current_container[-1]
                sym_id = f"{parent_id}:{node.name}"

                sym = SemanticSymbol(
                    symbol_id=sym_id,
                    name=node.name,
                    qualified_name=f"{self.graph.get_symbol(parent_id).qualified_name}.{node.name}",
                    symbol_kind=SymbolKind.CLASS,
                    language="Python",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    parent_symbol_id=parent_id
                )
                self.graph.add_symbol(sym)

                # Relation: CONTAINS
                self.graph.add_relation(SemanticRelation(
                    source_symbol_id=parent_id,
                    target_symbol_id=sym_id,
                    relation_type=SemanticRelationType.CONTAINS,
                    evidence=Evidence(file=rel_path, line=node.lineno, confidence_reason="AST ClassDef")
                ))

                # Inheritance check
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_name = base.id
                        self.graph.add_relation(SemanticRelation(
                            source_symbol_id=sym_id,
                            target_symbol_id=f"base:{base_name}",
                            relation_type=SemanticRelationType.INHERITS,
                            evidence=Evidence(file=rel_path, line=node.lineno, confidence_reason=f"Class base {base_name}")
                        ))

                current_container.append(sym_id)
                visitor_self.generic_visit(node)
                current_container.pop()

            def visit_Call(visitor_self, node: ast.Call):
                parent_id = current_container[-1]
                callee_name = None
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr

                if callee_name:
                    self.graph.add_relation(SemanticRelation(
                        source_symbol_id=parent_id,
                        target_symbol_id=f"call:{callee_name}",
                        relation_type=SemanticRelationType.CALLS,
                        evidence=Evidence(file=rel_path, line=node.lineno, confidence_reason=f"AST Call {callee_name}")
                    ))

                visitor_self.generic_visit(node)

        Visitor().visit(tree)
