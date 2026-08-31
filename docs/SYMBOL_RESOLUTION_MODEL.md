# Symbol Resolution Model

## 1. Resolution Logic
`SemanticResolver` searches `SemanticRepositoryGraph` to resolve symbol definitions:
1. **`RESOLVED`**: Unique symbol definition found or exact context match within current file.
2. **`AMBIGUOUS`**: Multiple symbol candidates exist across modules without a unique scope context.
3. **`UNRESOLVED`**: Symbol name is not found anywhere in the indexed workspace.
4. **`UNSUPPORTED`**: Dynamic symbol dispatch (`getattr`, `eval`) or unparsed language syntax.
