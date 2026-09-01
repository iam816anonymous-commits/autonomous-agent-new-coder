import ast
import os
from typing import Dict, Any, List, Set

class PythonDynamicDetector:
    """
    Detects dynamic Python constructs (getattr, eval, exec, importlib, star imports, monkey patching)
    that obscure static symbol visibility and trigger trust reduction.
    """
    @classmethod
    def detect_dynamic_constructs(cls, file_content: str, rel_path: str) -> List[Dict[str, Any]]:
        dynamic_findings = []

        try:
            tree = ast.parse(file_content, filename=rel_path)
        except Exception:
            return [{"type": "UNPARSABLE_SYNTAX", "file": rel_path, "line": 0, "reason": "SyntaxError in source file"}]

        class DynamicVisitor(ast.NodeVisitor):
            def visit_Call(visitor_self, node: ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("getattr", "setattr", "eval", "exec", "__import__"):
                    dynamic_findings.append({
                        "type": "DYNAMIC_FUNCTION_CALL",
                        "function": func_name,
                        "file": rel_path,
                        "line": node.lineno,
                        "reason": f"Use of dynamic function '{func_name}' obscuring static calls."
                    })
                elif func_name and ("import_module" in func_name or "importlib" in func_name):
                    dynamic_findings.append({
                        "type": "DYNAMIC_IMPORT",
                        "function": func_name,
                        "file": rel_path,
                        "line": node.lineno,
                        "reason": "Dynamic module import via importlib."
                    })

                visitor_self.generic_visit(node)

            def visit_ImportFrom(visitor_self, node: ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        dynamic_findings.append({
                            "type": "STAR_IMPORT",
                            "module": node.module or "",
                            "file": rel_path,
                            "line": node.lineno,
                            "reason": "Star import ('from ... import *') prevents explicit symbol mapping."
                        })

        DynamicVisitor().visit(tree)
        return dynamic_findings
