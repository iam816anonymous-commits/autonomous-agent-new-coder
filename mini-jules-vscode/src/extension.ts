import * as vscode from 'vscode';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => provider.sendCommand('generate')),
        vscode.commands.registerCommand('MiniJules.Manifest', () => provider.sendCommand('show_manifest'))
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

        webviewView.webview.onDidReceiveMessage(data => {
            if (data.type === 'api_call') {
                this._handleApi(data.endpoint, data.body);
            }
        });
    }

    public sendCommand(cmd: string) {
        this._view?.webview.postMessage({ type: 'command', value: cmd });
    }

    private async _handleApi(endpoint: string, body: any) {
        console.log(`VSCode Bridge: \${endpoint}`, body);
        // Logic to fetch(http://localhost:8000 + endpoint)
    }

    private _getHtml() {
        return `<html><body>
            <h3>Unified Jules</h3>
            <button onclick="call('start', {goal:'App', name:'my_app'})">Start Project</button>
            <div id="log"></div>
            <script>
                const vscode = acquireVsCodeApi();
                function call(endpoint, body) {
                    document.getElementById('log').innerText = 'Calling ' + endpoint;
                    vscode.postMessage({ type: 'api_call', endpoint, body });
                }
            </script>
        </body></html>`;
    }
}
