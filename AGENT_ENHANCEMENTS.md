# 🚀 Mini Jules Agent Enhancements

Detailed technical reference for the Tier 1 autonomous engineering enhancements.

## 📁 New Components

### 1. Dialogue Agent (`project_creator/agents/dialogue_agent.py`)
Gather requirements through a structured 7-question multi-turn conversation.
- **`gather_requirements(goal)`**: Conducts the dialogue and returns a summarized JSON.
- **`validate_architecture(blueprint)`**: Cross-references the blueprint with requirements.

### 2. Dependency Analyzer (`project_creator/brain/dependency_analyzer.py`)
Determines the correct generation order to prevent "Module Not Found" errors.
- **`get_dependency_order()`**: Uses topological sorting to order file generation.
- **`analyze_project()`**: Maps inter-file relationships based on descriptions.

### 3. Test Executor (`project_creator/core/test_executor.py`)
Automated verification of generated code behavior.
- **`run_tests()`**: Executes whitelisted test frameworks (pytest, npm, cargo).
- **`classify_failure(stderr)`**: Identifies failure types (IMPORT, SYNTAX, LOGIC).

### 4. Error Classifier (`project_creator/core/error_classifier.py`)
Heuristic-based error categorization.
- **`classify_error(message)`**: Assigns category (10 types) and severity (LOW-CRITICAL).
- **`get_repair_plan(category)`**: Suggests specific architectural fixes for each error type.

## 🛠️ Orchestrator Methods

- **`gather_requirements(goal)`**: Main entry point for the dialogue system.
- **`validate_architecture_with_user(architecture)`**: Human-in-the-loop validation of the plan.
- **`generate_with_dependency_order()`**: Executes generation following the topological sort.
- **`run_tests_with_repair(max_repair_cycles)`**: Closed-loop testing and repair.

## 🔄 Error Recovery Workflow
1. **Detection**: Test Executor finds a failure.
2. **Classification**: Error Classifier determines it's a `CIRCULAR_DEP`.
3. **Reasoning**: Brain suggests a 'Refactor to common core' strategy.
4. **Repair**: Repair Agent applies the suggested strategy.
5. **Validation**: Test Executor re-runs tests to confirm success.
