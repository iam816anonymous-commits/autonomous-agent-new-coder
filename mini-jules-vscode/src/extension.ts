import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    vscode.commands.registerCommand('MiniJules.ClearMemory', () => {
        vscode.window.showWarningMessage('Are you sure you want to delete all learned patterns?', 'Yes', 'No')
            .then(selection => {
                if (selection === 'Yes') {
                    // Call backend /clear_memory
                }
            });
    });
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
                body { font-family: sans-serif; padding: 10px; color: var(--vscode-foreground); }
                .tab { display: inline-block; padding: 5px; cursor: pointer; border-bottom: 2px solid transparent; }
                .tab.active { border-bottom: 2px solid var(--vscode-button-background); }
                .item { border: 1px solid #444; padding: 5px; margin-top: 5px; border-radius: 2px; }
                .forget { color: #f44; cursor: pointer; float: right; font-size: 10px; }
            </style>
        </head>
        <body>
            <div class="tab active">Brain</div>
            <div class="tab">Patterns</div>

            <div id="Brain">
                <h4>Top Imports</h4>
                <div class="item">fastapi <span class="forget">Forget</span></div>
                <div class="item">pydantic <span class="forget">Forget</span></div>

                <h4>Coding Style</h4>
                <div class="item">snake_case</div>
            </div>

            <button style="margin-top:20px; width:100%">Export Training Data</button>
        </body></html>`;
    }
}
