import * as vscode from 'vscode';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    // Command IDs must match package.json and codelens.ts
    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', (uri?: vscode.Uri) => {
            const target = uri ? uri.fsPath : 'workspace';
            provider.postMessage({ type: 'start_generate', target });
        }),
        vscode.commands.registerCommand('MiniJules.Critique', (uri?: vscode.Uri) => {
            provider.postMessage({ type: 'start_critique', target: uri?.fsPath });
        }),
        vscode.commands.registerCommand('MiniJules.Repair', (uri?: vscode.Uri) => {
            provider.postMessage({ type: 'start_repair', target: uri?.fsPath });
        }),
        vscode.commands.registerCommand('MiniJules.Manifest', () => {
             provider.postMessage({ type: 'show_manifest' });
        })
    );

    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ pattern: '**/*' }, new JulesCodeLensProvider())
    );

    vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) updateContext(editor);
    });

    async function updateContext(editor: vscode.TextEditor) {
        const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);
        const ctx = {
            active_file: editor.document.fileName,
            open_tabs: vscode.window.tabGroups.all.map(g => g.tabs.map(t => t.label)).flat(),
            diagnostics: diagnostics.map(d => d.message)
        };
        // This would be a real fetch to localhost:8000/ingest_context
        console.log('Ingesting Context:', ctx);
    }
}

class JulesViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'mini-jules-sidebar';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = `<html><body><h3>Mini Jules Active</h3></body></html>`;
    }

    public postMessage(msg: any) {
        this._view?.webview.postMessage(msg);
    }
}
