import * as vscode from 'vscode';
import { showDiff } from './bridge';

export function activate(context: vscode.ExtensionContext) {
    const provider = new JulesViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(JulesViewProvider.viewType, provider)
    );

    // Register Mini Jules Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('MiniJules.Generate', () => {
            provider.postMessage({ type: 'start_generate' });
        }),
        vscode.commands.registerCommand('MiniJules.Critique', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                const path = editor.document.fileName;
                const content = editor.document.getText();
                provider.postMessage({ type: 'critique_request', path, content });
            }
        }),
        vscode.commands.registerCommand('MiniJules.Repair', () => {
             provider.postMessage({ type: 'repair_request' });
        }),
        vscode.commands.registerCommand('MiniJules.ApplyPatch', async (patch: any) => {
             // Logic to call backend /apply_patch
             vscode.window.showInformationMessage(`Applying patch to ${patch.file}`);
        }),
        vscode.commands.registerCommand('MiniJules.Manifest', () => {
             provider.showTab('Manifest');
        })
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
            if (data.type === 'show_diff') {
                showDiff(data.oldContent, data.newContent, data.path);
            }
            if (data.type === 'tab') {
                console.log(`Switched to tab: \${data.value}`);
            }
        });
    }

    public postMessage(msg: any) {
        this._view?.webview.postMessage(msg);
    }

    public showTab(tab: string) {
        this.postMessage({ type: 'switch_tab', tab });
    }

    private _getHtml() {
        return `<!DOCTYPE html>
        <html>
        <head>
            <style>
                .tab-bar { display: flex; gap: 5px; margin-bottom: 10px; }
                button { cursor: pointer; }
                #content { border-top: 1px solid #ccc; padding-top: 10px; }
            </style>
        </head>
        <body>
            <div class="tab-bar">
                <button onclick="tab('Blueprint')">Blueprint</button>
                <button onclick="tab('Files')">Files</button>
                <button onclick="tab('Patches')">Patches</button>
                <button onclick="tab('Manifest')">Manifest</button>
            </div>
            <div id="content">Mini Jules Sidebar Active</div>
            <script>
                const vscode = acquireVsCodeApi();
                function tab(t) {
                    document.getElementById('content').innerText = t + ' View';
                    vscode.postMessage({ type: 'tab', value: t });
                }
            </script>
        </body></html>`;
    }
}
