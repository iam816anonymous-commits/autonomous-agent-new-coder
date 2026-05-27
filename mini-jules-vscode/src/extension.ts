import * as vscode from 'vscode';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => provider.sendCommand('generate')),
        vscode.commands.registerCommand('MiniJules.Manifest', () => provider.sendCommand('manifest'))
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
        webviewView.webview.html = this._getHtml();
    }

    public sendCommand(cmd: string) {
        this._view?.webview.postMessage({ type: 'command', value: cmd });
    }

    private _getHtml() {
        return `<html>
        <head>
            <style>
                body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 10px; font-size: 11px; }
                .status-tag { display: inline-block; padding: 2px 6px; border-radius: 2px; background: #0e639c; color: white; margin-bottom: 10px; }
                .card { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); padding: 8px; margin-top: 10px; }
                .sec-pass { color: #89d185; }
                .sec-info { opacity: 0.7; }
                h3 { margin-top: 0; }
            </style>
        </head>
        <body>
            <div class="status-tag">🛡️  Constitutional Sandbox Active</div>
            <div class="card">
                <h3>Mini Jules Pro</h3>
                <p class="sec-info">Ecosystem Health: <span class="sec-pass">98% Stable</span></p>
                <button style="width:100%; cursor:pointer" onclick="vscode.postMessage({type:'plan'})">New Project</button>
            </div>
            <script>const vscode = acquireVsCodeApi();</script>
        </body></html>`;
    }
}
