# Python Dynamic Analysis Limitations

## 1. Dynamic Features
Dynamic Python constructs obscure static symbol resolution:
* `getattr()`, `setattr()`, `hasattr()`
* `eval()`, `exec()`
* `importlib.import_module()`
* `from module import *`
* Monkey patching & dynamic class creation

## 2. Mitigation Strategy
`PythonDynamicDetector` detects these patterns and degrades confidence scores to `LOW_CONFIDENCE` or `UNKNOWN`, forcing discovery or fail-closed behavior rather than guessing.
