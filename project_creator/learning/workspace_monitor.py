import os
import time
from .event_bus import bus
from project_creator.core.manifest import ProjectManifest

class WorkspaceMonitor:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.manifest = ProjectManifest(workspace_root)
        self.last_check = {}

    def scan_for_deltas(self):
        """
        Compares disk content with manifest content to detect user edits to Jules' code.
        """
        data = self.manifest.load()
        if not data or 'project' not in data or 'files' not in data['project']:
            return

        for path, meta in data['project']['files'].items():
            if meta.get('status') != 'applied':
                continue

            full_path = os.path.join(self.workspace_root, path)
            if not os.path.exists(full_path):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()

                # We need the last version Jules wrote.
                # For this impl, we'll look for the latest session state or store it in manifest.
                # Assuming SessionManager keeps the "Last Jules Version".
                from project_creator.core.session import SessionManager
                session = SessionManager(self.workspace_root)
                sess_data = session.load_session()

                if sess_data and path in sess_data.get('generated_files', {}):
                    jules_version = sess_data['generated_files'][path]

                    if current_content != jules_version:
                        # Detection!
                        bus.publish("MANUAL_EDIT_DETECTED", {
                            "path": path,
                            "jules_code": jules_version,
                            "user_code": current_content
                        })
                        print(f"🕵️  WorkspaceMonitor: Detected manual edit in {path}")

                        # Update jules_version to avoid repeated triggers
                        # In a real app, we'd only do this after learning is confirmed
            except Exception as e:
                print(f"⚠️  Monitor error on {path}: {e}")
