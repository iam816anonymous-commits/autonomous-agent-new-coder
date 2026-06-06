import * as vscode from 'vscode';
import { JulesCodeLensProvider } from './codelens';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    // Register CodeLens
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider(
            { scheme: 'file', language: 'python' },
            new JulesCodeLensProvider()
        )
    );

    // Register Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', async (args) => {
            vscode.window.showInformationMessage(`Mini Jules: Generating for ${args?.path || 'workspace'}...`);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Repair', async (args) => {
            vscode.window.showInformationMessage(`Mini Jules: Repairing ${args?.path}...`);
        })
    );
}

class JulesViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'mini-jules-sidebar';
    private _view?: vscode.WebviewView;
    private readonly _baseUrl = 'http://127.0.0.1:8000';

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this._getHtml();

        webviewView.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'refresh':
                    await this._refreshStats();
                    await this._refreshPatterns();
                    break;
                case 'deletePattern':
                    await fetch(`${this._baseUrl}/learning/patterns/${message.id}`, { method: 'DELETE' });
                    await this._refreshPatterns();
                    break;
                case 'updatePattern':
                    await fetch(`${this._baseUrl}/learning/patterns/${message.id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content: message.content })
                    });
                    break;
                case 'exportLora':
                    const res = await fetch(`${this._baseUrl}/learning/export`, {
                        method: 'POST',
                        body: '{}',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const data = await res.json();
                    vscode.window.showInformationMessage(`Exported ${data.count} examples to ${data.path}`);
                    break;
            }
        });
    }

    private async _refreshStats() {
        try {
            const res = await fetch(`${this._baseUrl}/learning/stats`);
            const data = await res.json();
            this._view?.webview.postMessage({ type: 'updateStats', data: data });
        } catch (e) {}
    }

    private async _refreshPatterns() {
        try {
            const res = await fetch(`${this._baseUrl}/learning/patterns`);
            const data = await res.json();
            this._view?.webview.postMessage({ type: 'updatePatterns', data: data });
        } catch (e) {}
    }

    private _getHtml() {
        return `<html>
        <head>
            <style>
                body { font-family: sans-serif; padding: 10px; color: var(--vscode-foreground); font-size: 12px; }
                .tabs { display: flex; border-bottom: 1px solid #333; margin-bottom: 10px; }
                .tab { padding: 5px 10px; cursor: pointer; opacity: 0.7; }
                .tab.active { border-bottom: 2px solid var(--vscode-button-background); opacity: 1; }
                .content { display: none; }
                .content.active { display: block; }
                .night-tag { background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 4px; border-left: 4px solid #cc99cd; }
                .stat { margin-top: 5px; opacity: 0.8; }
                .value { float: right; color: var(--vscode-button-background); font-weight: bold; }
                .pattern-item { padding: 5px; border-bottom: 1px solid #222; }
                .delete-btn { color: #f44; cursor: pointer; float: right; }
            </style>
        </head>
        <body>
            <div class="tabs">
                <div class="tab active" onclick="showTab('stats')">Stats</div>
                <div class="tab" onclick="showTab('patterns')">Patterns</div>
            </div>

            <div id="stats" class="content active">
                <div class="night-tag">
                    <h3>🌙 Night Learning</h3>
                    <div id="stats-container">Loading...</div>
                    <button onclick="exportLora()" style="margin-top: 10px; width: 100%;">Export LoRA Dataset</button>
                </div>
            </div>

            <div id="patterns" class="content">
                <h3>🧠 Learned Patterns</h3>
                <div id="patterns-container">Loading...</div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                function showTab(id) {
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
                    document.querySelector(\`[onclick="showTab('\${id}')"]\`).classList.add('active');
                    document.getElementById(id).classList.add('active');
                }

                window.addEventListener('message', event => {
                    const message = event.data;
                    if (message.type === 'updateStats') {
                        document.getElementById('stats-container').innerHTML = \`
                            <div class="stat">Tasks Completed: <span class="value">\${message.data.tasks || 0}</span></div>
                            <div class="stat">Patterns Learned: <span class="value">\${message.data.patterns || 0}</span></div>
                            <div class="stat">Memory Growth: <span class="value">\${message.data.memory_growth || '0 KB'}</span></div>
                        \`;
                    } else if (message.type === 'updatePatterns') {
                        document.getElementById('patterns-container').innerHTML = message.data.map(p => \`
                            <div class="pattern-item">
                                <b>${p.pattern_type}</b>:
                                <span id="content-${p.id}" contenteditable="true" onblur="updatePattern(${p.id})">${p.content}</span>
                                (${p.frequency})
                                <span class="delete-btn" onclick="deletePattern(\${p.id})">🗑️</span>
                            </div>
                        \`).join('');
                    }
                });

                function deletePattern(id) {
                    vscode.postMessage({ command: 'deletePattern', id: id });
                }

                function updatePattern(id) {
                    const newContent = document.getElementById(\`content-\${id}\`).innerText;
                    vscode.postMessage({ command: 'updatePattern', id: id, content: newContent });
                }

                function exportLora() {
                    vscode.postMessage({ command: 'exportLora' });
                }

                // Initial load
                vscode.postMessage({ command: 'refresh' });
            </script>
        </body></html>`;
    }
}
