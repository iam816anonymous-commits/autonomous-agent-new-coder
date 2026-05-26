import * as vscode from 'vscode';

export class JulesCodeLensProvider implements vscode.CodeLensProvider {
    public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): vscode.CodeLens[] {
        const lenses: vscode.CodeLens[] = [];
        const topRange = new vscode.Range(0, 0, 0, 0);

        lenses.push(new vscode.CodeLens(topRange, {
            title: "$(sparkle) Generate Here",
            command: "MiniJules.Generate",
            arguments: [document.uri]
        }));

        lenses.push(new vscode.CodeLens(topRange, {
            title: "$(bug) Repair File",
            command: "MiniJules.Repair",
            arguments: [document.uri]
        }));

        lenses.push(new vscode.CodeLens(topRange, {
            title: "$(eye) Critique File",
            command: "MiniJules.Critique",
            arguments: [document.uri]
        }));

        return lenses;
    }
}
