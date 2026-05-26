import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Mini Jules Extension is now active');

    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('mini-jules.generate', () => {
            vscode.window.showInformationMessage('Mini Jules: Starting Project Generation...');
        })
    );
}

class JulesViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'mini-jules-sidebar';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(data => {
            switch (data.type) {
                case 'prompt':
                    // Bridge to backend
                    vscode.window.showInformationMessage(`Jules Planning: ${data.value}`);
                    break;
            }
        });
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
            <html lang="en">
            <body>
                <h2>Mini Jules</h2>
                <input type="text" id="goal" placeholder="What to build?">
                <button onclick="send()">Plan</button>
                <div id="status">Ready</div>

                <script>
                    const vscode = acquireVsCodeApi();
                    function send() {
                        const val = document.getElementById('goal').value;
                        vscode.postMessage({ type: 'prompt', value: val });
                    }
                </script>
            </body>
            </html>`;
    }
}
