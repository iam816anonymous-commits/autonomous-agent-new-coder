# Pre-Execution Validation

## 1. Pre-Execution Assertions
`PreExecutionValidator` executes pre-flight assertions immediately before applying changes:
1. `ASSERT_FILE_EXISTS_IN_WORKSPACE`: Target file exists and does not escape workspace realpath boundaries.
2. `ASSERT_SYMBOL_EXISTS`: Target symbol is present in `SemanticRepositoryGraph`.
3. Fails closed with `PreExecutionAssertionError` if workspace drift has occurred.
