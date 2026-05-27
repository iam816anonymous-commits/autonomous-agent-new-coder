import * as vscode from 'vscode';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    // Final Frozen Command Set
    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => provider.triggerAction('Generate')),
        vscode.commands.registerCommand('MiniJules.Critique', () => provider.triggerAction('Critique')),
        vscode.commands.registerCommand('MiniJules.Repair', () => provider.triggerAction('Repair')),
        vscode.commands.registerCommand('MiniJules.ApplyPatch', () => provider.triggerAction('ApplyPatch')),
        vscode.commands.registerCommand('MiniJules.Manifest', () => provider.triggerAction('Manifest'))
    );

    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ pattern: '**/*' }, new JulesCodeLensProvider())
    );
}

class JulesViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'mini-jules-sidebar';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true, localResourceRoots: [this._extensionUri] };
        webviewView.webview.html = `<html><body><h3>Mini Jules Production</h3></body></html>`;
    }

    public triggerAction(action: string) {
        this._view?.webview.postMessage({ type: 'action', value: action });
    }
}
