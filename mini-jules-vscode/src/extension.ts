import * as vscode from 'vscode';
import { showDiff } from './bridge';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => provider.startAction('Generate')),
        vscode.commands.registerCommand('MiniJules.Critique', () => provider.startAction('Critique')),
        vscode.commands.registerCommand('MiniJules.Repair', () => provider.startAction('Repair')),
        vscode.commands.registerCommand('MiniJules.Manifest', () => provider.showTab('Manifest'))
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
        webviewView.webview.html = this._getHtml(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'plan':
                    vscode.window.showInformationMessage(`Jules: Planning \${data.goal}...`);
                    break;
                case 'approve_patch':
                    // Interaction logic
                    break;
            }
        });
    }

    public startAction(action: string) {
        this._view?.webview.postMessage({ type: 'action', value: action });
    }

    public showTab(tab: string) {
        this._view?.webview.postMessage({ type: 'switch_tab', value: tab });
    }

    private _getHtml(webview: vscode.Webview) {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 10px; }
                .tab-header { display: flex; border-bottom: 1px solid var(--vscode-panel-border); margin-bottom: 15px; }
                .tab-btn { background: none; border: none; color: var(--vscode-tab-inactiveForeground); padding: 5px 10px; cursor: pointer; }
                .tab-btn.active { color: var(--vscode-tab-activeForeground); border-bottom: 2px solid var(--vscode-button-background); }
                .card { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); border-radius: 4px; padding: 10px; margin-bottom: 10px; }
                input, button { width: 100%; margin-top: 5px; padding: 8px; box-sizing: border-box; }
                button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; cursor: pointer; }
                button:hover { background: var(--vscode-button-hoverBackground); }
            </style>
        </head>
        <body>
            <div class="tab-header">
                <button class="tab-btn active" onclick="show('Blueprint')">Blueprint</button>
                <button class="tab-btn" onclick="show('Timeline')">Timeline</button>
                <button class="tab-btn" onclick="show('Manifest')">Manifest</button>
            </div>

            <div id="Blueprint">
                <div class="card">
                    <h3>New Project</h3>
                    <input type="text" id="goal" placeholder="e.g. FastAPI SaaS">
                    <button onclick="plan()">Generate Plan</button>
                </div>
            </div>

            <div id="Timeline" style="display:none">
                <div class="card">No active tasks.</div>
            </div>

            <div id="Manifest" style="display:none">
                <pre id="manifest-content">{}</pre>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                function show(id) {
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    ['Blueprint', 'Timeline', 'Manifest'].forEach(div => document.getElementById(div).style.display = div === id ? 'block' : 'none');
                    event.target.classList.add('active');
                }
                function plan() {
                    const goal = document.getElementById('goal').value;
                    vscode.postMessage({ type: 'plan', goal });
                }
            </script>
        </body>
        </html>`;
    }
}
