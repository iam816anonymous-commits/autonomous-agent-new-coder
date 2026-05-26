import * as vscode from 'vscode';
import { showDiff } from './bridge';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => provider.triggerAction('Generate')),
        vscode.commands.registerCommand('MiniJules.Critique', () => provider.triggerAction('Critique')),
        vscode.commands.registerCommand('MiniJules.Repair', () => provider.triggerAction('Repair')),
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
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        webviewView.webview.html = this._getHtml(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            try {
                switch (data.type) {
                    case 'request_plan':
                        const res = await this._callBackend('/plan', { goal: data.goal });
                        this._view?.webview.postMessage({ type: 'blueprint', value: res });
                        break;
                    case 'approve_file':
                        await this._callBackend('/apply', { path: data.path, content: data.content });
                        vscode.window.showInformationMessage(`Applied: \${data.path}`);
                        break;
                }
            } catch (e) {
                vscode.window.showErrorMessage(`Backend Error: \${e}`);
            }
        });
    }

    public triggerAction(action: string) {
        this._view?.webview.postMessage({ type: 'action', value: action });
    }

    private async _callBackend(endpoint: string, body: any) {
        // In a real extension, we would use axios or fetch to localhost:8000
        console.log('Calling backend:', endpoint, body);
        return { status: 'mocked' };
    }

    private _getHtml(webview: vscode.Webview) {
        return `<!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: sans-serif; padding: 10px; color: #ccc; }
                .btn { background: #007acc; color: white; border: none; padding: 8px; width: 100%; cursor: pointer; border-radius: 2px; }
                .input { width: 100%; padding: 8px; margin: 10px 0; background: #333; color: white; border: 1px solid #555; box-sizing: border-box; }
                .card { border: 1px solid #444; padding: 10px; margin-top: 10px; border-radius: 4px; }
                .tab-bar { display: flex; border-bottom: 1px solid #444; margin-bottom: 10px; }
                .tab { padding: 5px 10px; cursor: pointer; font-size: 12px; }
                .tab.active { border-bottom: 2px solid #007acc; color: white; }
            </style>
        </head>
        <body>
            <div class="tab-bar">
                <div class="tab active" onclick="tab('plan')">Plan</div>
                <div class="tab" onclick="tab('status')">Status</div>
            </div>
            <div id="plan-view">
                <h3>Architecture</h3>
                <input class="input" id="goal" placeholder="What shall we build?">
                <button class="btn" onclick="sendPlan()">Architect Project</button>
                <div id="blueprint-list"></div>
            </div>
            <script>
                const vscode = acquireVsCodeApi();
                function tab(n) { console.log('tab', n); }
                function sendPlan() {
                    const goal = document.getElementById('goal').value;
                    vscode.postMessage({ type: 'request_plan', goal });
                }
                window.addEventListener('message', event => {
                    const msg = event.data;
                    if(msg.type === 'blueprint') {
                        document.getElementById('blueprint-list').innerHTML = '<p>Plan received!</p>';
                    }
                });
            </script>
        </body>
        </html>`;
    }
}
