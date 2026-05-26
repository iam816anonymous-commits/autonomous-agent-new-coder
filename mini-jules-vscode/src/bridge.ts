import * as vscode from 'vscode';
import * as os from 'os';
import * as path from 'path';

export async function showDiff(oldContent: string, newContent: string, fileName: string) {
    // Cross-platform temporary file handling
    const tempDir = os.tmpdir();
    const tempFilePath = path.join(tempDir, `jules_candidate_${path.basename(fileName)}`);
    const tempUri = vscode.Uri.file(tempFilePath);

    await vscode.workspace.fs.writeFile(tempUri, Buffer.from(newContent));

    await vscode.commands.executeCommand('vscode.diff',
        vscode.Uri.file(fileName),
        tempUri,
        `Jules Patch: ${fileName}`
    );
}

export function scanWorkspace() {
    // Call backend API /scan
    return [];
}
