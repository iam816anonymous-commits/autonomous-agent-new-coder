# Confidence Calibration

## 1. Deterministic Calibration Factors
`ConfidenceCalibrator` calculates numerical confidence scores (0.0 to 1.0) deterministically:
* Base AST evidence: +1.0
* Heuristic match penalty: -0.3
* Ambiguous candidates penalty: -0.3
* Dynamic attribute access (`getattr`) penalty: -0.4
* Star import (`from ... import *`) penalty: -0.3
