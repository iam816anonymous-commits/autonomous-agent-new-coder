# 🟦 Mini Jules VS Code Extension

The official VS Code interface for the Mini Jules autonomous engineering agent.

## ✨ Features

### Sidebar Webview
- **Blueprint Tab**: Start new projects and refine architectures.
- **Timeline Tab**: Track the progress of generation and repair tasks.
- **Manifest Tab**: View the live `project.yaml` source of truth.

### Inline Actions (CodeLens)
- **Generate Here**: Trigger context-aware code generation directly in the editor.
- **Repair File**: Automatically fix diagnostics or audit issues in the active file.
- **Critique File**: Run a senior-level audit on your code.

### Native Diff Review
Mini Jules leverages VS Code's native `vscode.diff` command for all patch approvals, ensuring you always see exactly what is about to be applied.

## 🛠️ Development

1. `npm install`
2. `npm run watch` (for auto-compilation)
3. Press `F5` to open the Extension Development Host.

Requires the [Mini Jules Backend](../project_creator) to be running on `localhost:8000`.
