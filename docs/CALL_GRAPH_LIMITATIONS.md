# Call Graph Limitations

## 1. Conservative Resolution
Dynamic Python features mean call graphs cannot achieve 100% resolution statically. `ConservativeCallGraph` categorizes call relationships into explicit confidence levels:
* **`HIGH`**: AST unique function call within scope.
* **`MEDIUM`**: Unambiguous imported function call.
* **`LOW`**: Attribute method call on dynamic object without static type annotation.
* **`UNKNOWN`**: Reflection, `getattr()`, or dynamic dispatch.
