import * as vscode from 'vscode';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => provider.triggerAction('Generate')),
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
             // Unified API handler
             console.log('Webview Message:', data);
        });
    }

    public triggerAction(action: string) {
        this._view?.webview.postMessage({ type: 'action', value: action });
    }

    private _getHtml(webview: vscode.Webview) {
        return `<!DOCTYPE html>
        <html>
        <head>
            <style>
                :root {
                    --bg: var(--vscode-sideBar-background);
                    --fg: var(--vscode-sideBar-foreground);
                    --btn-bg: var(--vscode-button-background);
                    --btn-fg: var(--vscode-button-foreground);
                }
                body { font-family: var(--vscode-font-family); padding: 12px; color: var(--fg); background: var(--bg); font-size: var(--vscode-font-size); }
                .tab-header { display: flex; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--vscode-panel-border); }
                .tab { padding: 4px 8px; cursor: pointer; opacity: 0.7; }
                .tab.active { opacity: 1; border-bottom: 2px solid var(--btn-bg); color: var(--vscode-button-background); font-weight: bold; }
                .input-group { margin-bottom: 12px; }
                label { display: block; margin-bottom: 4px; font-size: 11px; text-transform: uppercase; }
                input { width: 100%; padding: 6px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); box-sizing: border-box; }
                button { width: 100%; padding: 8px; background: var(--btn-bg); color: var(--btn-fg); border: none; border-radius: 2px; cursor: pointer; }
                button:hover { background: var(--vscode-button-hoverBackground); }
                .card { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); padding: 8px; border-radius: 4px; margin-top: 8px; }
            </style>
        </head>
        <body>
            <div class="tab-header">
                <div class="tab active" onclick="setTab('Plan')">Plan</div>
                <div class="tab" onclick="setTab('Queue')">Queue</div>
                <div class="tab" onclick="setTab('Meta')">Meta</div>
            </div>

            <div id="Plan">
                <div class="input-group">
                    <label>Build Objective</label>
                    <input id="goal" placeholder="e.g. CLI Scraper">
                </div>
                <button onclick="start()">Initialize Architect</button>
            </div>

            <div id="Queue" style="display:none">
                <div class="card">No files pending review.</div>
            </div>

            <div id="Meta" style="display:none">
                <label>Project Manifest</label>
                <div class="card" id="manifest">Ready.</div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                function setTab(name) {
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    ['Plan', 'Queue', 'Meta'].forEach(id => document.getElementById(id).style.display = id === name ? 'block' : 'none');
                    event.target.classList.add('active');
                }
                function start() {
                    const goal = document.getElementById('goal').value;
                    vscode.postMessage({ type: 'api', endpoint: '/start', body: { goal, name: 'project' } });
                }
            </script>
        </body>
        </html>`;
    }
}
