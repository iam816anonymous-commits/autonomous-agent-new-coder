import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );
}

class JulesViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'mini-jules-sidebar';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this._getHtml();
    }

    private _getHtml() {
        return `<html>
        <head>
            <style>
                body { font-family: sans-serif; padding: 10px; color: var(--vscode-foreground); font-size: 12px; }
                .night-tag { background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 4px; border-left: 4px solid #cc99cd; }
                .stat { margin-top: 5px; opacity: 0.8; }
                .value { float: right; color: var(--vscode-button-background); font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="night-tag">
                <h3>🌙 Night Learning</h3>
                <div class="stat">Tasks Completed: <span class="value">12</span></div>
                <div class="stat">Patterns Learned: <span class="value">42</span></div>
                <div class="stat">Quota Used: <span class="value">340</span></div>
                <div class="stat">Memory Growth: <span class="value">1.2 MB</span></div>
            </div>
        </body></html>`;
    }
}
