# 🏁 Mini Jules Quick Start Guide

Get up and running with the enhanced autonomous agent in under 10 minutes.

## 🛠️ Setup

### 1. Requirements
Ensure you have Python 3.10+ and the required packages:
```bash
pip install -r requirements.txt
```

### 2. Environment
Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
```

## 🚀 The Enhanced Workflow

### Run the Demo
The fastest way to see the new components in action:
```bash
python examples/enhanced_workflow.py
```

### Components Deep Dive

#### 1. Gathering Requirements
```python
requirements = orchestrator.gather_requirements("Build a secure API")
```

#### 2. Dependency Ordering
```python
# Before generation, get the order
order = orchestrator.dependency_analyzer.get_dependency_order()
print(order)
```

#### 3. Test-Driven Repair
```python
# Automatically runs pytest and attempts 3 repair cycles
orchestrator.run_tests_with_repair(max_repair_cycles=3)
```

## 💡 Troubleshooting

- **Module Not Found**: Ensure you are running from the repository root.
- **Empty Strategy**: The Brain requires historical data or a detailed initial goal.
- **Test Failures**: Check `agent_audit.log` for raw tool output.

---
*Ready to build? Use the `examples/enhanced_workflow.py` as your template.*
